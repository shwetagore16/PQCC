"""
ml_engine/gnn_attack_path.py — GNN Attack Path Simulation (PyTorch Geometric).

Architecture: GraphSAGE encoder → link predictor → CVSS-weighted shortest-path.

Pipeline:
  1. Build a PyTorch Geometric HeteroData / Data graph from Neo4j topology.
  2. Run GraphSAGE to produce node embeddings.
  3. Use link-prediction head to score each directed edge as an 'attack edge'.
  4. Apply CVSS weights to construct a weighted directed graph in NetworkX.
  5. Run Yen's k-shortest paths to enumerate the top exploit routes.
  6. Return ranked AttackPath objects with confidence and CVSS metadata.

GraphSAGE node feature vector (12 dims):
  [0]  hndl_score          — float [0,10]
  [1]  key_bits_norm       — float [0,1]  (key_bits / 8192)
  [2]  tls_version_int     — int   {0..5} (SSL2=0 … TLS1.3=5)
  [3]  supports_pqc_kem    — bool  {0,1}
  [4]  cert_expiry_days    — float [0,1]  (days_to_expiry / 365)
  [5]  tier_embedding      — int   {0..4} (internet=0, lb=1, web=2, api=3, db=4)
  [6]  open_ports_count    — float [0,1]  (count / 65535)
  [7]  vulnerability_count — float [0,1]  (cve_count / 100)
  [8]  avg_cvss_score      — float [0,1]  (cvss / 10)
  [9]  exposure_score      — float [0,1]
  [10] algo_risk_class     — int   {0..3} (safe=0 … broken=3)
  [11] migration_days      — float [0,1]  (migration_days / 3650)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

import networkx as nx
import numpy as np
import structlog
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor
from torch_geometric.data import Data
from torch_geometric.nn import SAGEConv

from ml_engine.schemas import AttackPath, AttackPathNode, AttackPathReport

logger = structlog.get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

NODE_FEATURE_DIM: int    = 12   # Dimensions of the input feature vector
HIDDEN_DIM:       int    = 64   # GraphSAGE hidden embedding dimension
OUT_DIM:          int    = 32   # Final node embedding dimension
NUM_SAGE_LAYERS:  int    = 3    # Depth of the GraphSAGE stack


# ─────────────────────────────────────────────────────────────────────────────
# GraphSAGE Encoder
# ─────────────────────────────────────────────────────────────────────────────

class GraphSAGEEncoder(nn.Module):
    """
    3-layer GraphSAGE encoder producing 32-dim node embeddings.

    Aggregation: 'mean' (suitable for variable-degree banking topology nodes).
    Each layer applies:  node_emb = ReLU( W * CONCAT(self_emb, mean_neighbour_emb) )
    """

    def __init__(
        self,
        in_channels:  int = NODE_FEATURE_DIM,
        hidden_channels: int = HIDDEN_DIM,
        out_channels: int = OUT_DIM,
        dropout:      float = 0.3,
    ) -> None:
        super().__init__()
        self.dropout = dropout

        self.conv1 = SAGEConv(in_channels,     hidden_channels, aggr="mean", normalize=True)
        self.conv2 = SAGEConv(hidden_channels, hidden_channels, aggr="mean", normalize=True)
        self.conv3 = SAGEConv(hidden_channels, out_channels,    aggr="mean", normalize=True)

        # Layer normalisation stabilises training on heterogeneous graph features
        self.ln1 = nn.LayerNorm(hidden_channels)
        self.ln2 = nn.LayerNorm(hidden_channels)

    def forward(self, x: Tensor, edge_index: Tensor) -> Tensor:
        """
        Args:
            x:          [N, in_channels] node feature matrix
            edge_index: [2, E] edge index (COO format)
        Returns:
            [N, out_channels] node embeddings
        """
        # Layer 1
        x = self.conv1(x, edge_index)
        x = self.ln1(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)

        # Layer 2
        x = self.conv2(x, edge_index)
        x = self.ln2(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)

        # Layer 3 — final embedding (no activation; downstream head applies softmax/sigmoid)
        x = self.conv3(x, edge_index)
        return x


# ─────────────────────────────────────────────────────────────────────────────
# Link Prediction Head
# ─────────────────────────────────────────────────────────────────────────────

class AttackLinkPredictor(nn.Module):
    """
    Bilinear + MLP link-prediction head.

    Given two node embeddings (source, target), predicts the probability that
    an attacker can exploit a TLS weak-crypto edge to laterally move from
    source to target.

    P(attack_edge | h_src, h_dst) = σ( MLP( CONCAT(h_src, h_dst, h_src ⊙ h_dst) ) )
    """

    def __init__(self, embedding_dim: int = OUT_DIM) -> None:
        super().__init__()
        in_dim = embedding_dim * 3  # concat + hadamard

        self.mlp = nn.Sequential(
            nn.Linear(in_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

    def forward(self, h_src: Tensor, h_dst: Tensor) -> Tensor:
        """
        Args:
            h_src: [E, embed_dim] source node embeddings
            h_dst: [E, embed_dim] target node embeddings
        Returns:
            [E] attack-edge probabilities (sigmoid-activated)
        """
        hadamard = h_src * h_dst
        combined = torch.cat([h_src, h_dst, hadamard], dim=-1)
        return torch.sigmoid(self.mlp(combined)).squeeze(-1)


# ─────────────────────────────────────────────────────────────────────────────
# Full GNN Model
# ─────────────────────────────────────────────────────────────────────────────

class AttackPathGNN(nn.Module):
    """
    Combined GraphSAGE encoder + attack link predictor.

    Typical usage::

        model = AttackPathGNN()
        model.load_state_dict(torch.load("weights/attack_gnn.pt"))
        model.eval()

        node_embs = model.encode(data.x, data.edge_index)
        scores    = model.predict_links(node_embs, candidate_edge_index)
    """

    def __init__(
        self,
        in_channels:  int   = NODE_FEATURE_DIM,
        hidden_dim:   int   = HIDDEN_DIM,
        out_dim:      int   = OUT_DIM,
        dropout:      float = 0.3,
    ) -> None:
        super().__init__()
        self.encoder   = GraphSAGEEncoder(in_channels, hidden_dim, out_dim, dropout)
        self.predictor = AttackLinkPredictor(out_dim)

    def encode(self, x: Tensor, edge_index: Tensor) -> Tensor:
        """Run the GraphSAGE encoder; returns node embeddings."""
        return self.encoder(x, edge_index)

    def predict_links(self, node_embs: Tensor, edge_index: Tensor) -> Tensor:
        """
        Predict attack-edge probabilities for candidate edges.

        Args:
            node_embs:  [N, out_dim] node embeddings from encode()
            edge_index: [2, E_candidate] candidate directed edges to score
        Returns:
            [E_candidate] probabilities in [0, 1]
        """
        src, dst = edge_index
        return self.predictor(node_embs[src], node_embs[dst])

    def forward(self, x: Tensor, edge_index: Tensor) -> Tensor:
        """Full forward pass: encode → predict links on training edges."""
        embs = self.encode(x, edge_index)
        return self.predict_links(embs, edge_index)


# ─────────────────────────────────────────────────────────────────────────────
# Graph Builder — Neo4j topology → PyG Data
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class NodeFeatureBuilder:
    """
    Constructs the 12-dim node feature vector from raw asset properties.

    All features are normalised to [0, 1] or {0, 1, 2, 3, ...} integer classes
    to ensure gradient stability during GNN training.
    """

    _TIER_MAP: dict[str, int] = field(default_factory=lambda: {
        "internet":     0,
        "loadbalancer": 1,
        "webserver":    2,
        "apiserver":    3,
        "database":     4,
    })
    _TLS_VERSION_MAP: dict[str, int] = field(default_factory=lambda: {
        "sslv2": 0, "sslv3": 1, "tlsv1.0": 2,
        "tlsv1.1": 3, "tlsv1.2": 4, "tlsv1.3": 5,
    })
    _ALGO_RISK_MAP: dict[str, int] = field(default_factory=lambda: {
        "quantum_safe": 0, "hybrid": 1, "classical": 2, "broken": 3,
    })

    def build(self, asset: dict[str, Any]) -> list[float]:
        """
        Build a 12-dim feature vector from an asset property dict.

        Expected keys in `asset`:
            hndl_score, key_bits, tls_version, supports_pqc_kem,
            cert_expiry_days, tier, open_ports_count, vulnerability_count,
            avg_cvss_score, exposure_score, algo_risk_class, migration_days
        """
        return [
            float(asset.get("hndl_score", 5.0)) / 10.0,
            float(asset.get("key_bits", 2048)) / 8192.0,
            float(self._TLS_VERSION_MAP.get(str(asset.get("tls_version", "tlsv1.2")).lower(), 4)) / 5.0,
            float(bool(asset.get("supports_pqc_kem", False))),
            min(1.0, float(asset.get("cert_expiry_days", 365)) / 365.0),
            float(self._TIER_MAP.get(str(asset.get("tier", "webserver")).lower().replace(" ", ""), 2)) / 4.0,
            min(1.0, float(asset.get("open_ports_count", 1)) / 65535.0),
            min(1.0, float(asset.get("vulnerability_count", 0)) / 100.0),
            float(asset.get("avg_cvss_score", 5.0)) / 10.0,
            float(asset.get("exposure_score", 0.5)),
            float(self._ALGO_RISK_MAP.get(str(asset.get("algo_risk_class", "classical")).lower(), 2)) / 3.0,
            min(1.0, float(asset.get("migration_days", 730)) / 3650.0),
        ]


def build_pyg_graph(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> tuple[Data, dict[int, str]]:
    """
    Convert a Neo4j topology result into a PyTorch Geometric Data object.

    Args:
        nodes:  List of asset property dicts (one per node).
                Must include 'asset_id' key.
        edges:  List of edge dicts with keys: 'from_id', 'to_id', 'cvss_score' (optional).

    Returns:
        (Data, id_map) where id_map maps integer node index → asset_id string.
    """
    builder = NodeFeatureBuilder()

    # Build node index
    asset_ids = [n["asset_id"] for n in nodes]
    id_to_idx: dict[str, int] = {aid: i for i, aid in enumerate(asset_ids)}
    idx_to_id: dict[int, str] = {i: aid for aid, i in id_to_idx.items()}

    # Feature matrix
    x = torch.tensor(
        [builder.build(n) for n in nodes],
        dtype=torch.float32,
    )   # [N, 12]

    # Edge index + CVSS edge weights
    src_list, dst_list, weights = [], [], []
    for e in edges:
        src_id, dst_id = e.get("from_id"), e.get("to_id")
        if src_id in id_to_idx and dst_id in id_to_idx:
            src_list.append(id_to_idx[src_id])
            dst_list.append(id_to_idx[dst_id])
            weights.append(float(e.get("cvss_score", 5.0)))

    edge_index  = torch.tensor([src_list, dst_list], dtype=torch.long)
    edge_weight = torch.tensor(weights, dtype=torch.float32)

    data = Data(x=x, edge_index=edge_index, edge_attr=edge_weight)
    return data, idx_to_id


# ─────────────────────────────────────────────────────────────────────────────
# Inference Engine
# ─────────────────────────────────────────────────────────────────────────────

class AttackPathSimulator:
    """
    High-level inference wrapper: GNN → scored edges → NetworkX shortest paths.

    Usage::

        simulator = AttackPathSimulator(model=trained_gnn)
        report = simulator.run(
            nodes=topology_nodes,
            edges=topology_edges,
            source_asset_id="<uuid>",
            target_tier="database",
            k_paths=10,
        )
    """

    def __init__(
        self,
        model: AttackPathGNN | None = None,
        device: str = "cpu",
        gnn_threshold: float = 0.35,
    ) -> None:
        """
        Args:
            model:         Pre-trained AttackPathGNN. If None, uses a randomly
                           initialised model (useful for topology-only analysis).
            device:        'cpu' or 'cuda'.
            gnn_threshold: Minimum link-prediction probability to include an edge
                           in the attack graph.
        """
        self.device = torch.device(device)
        self.model  = (model or AttackPathGNN()).to(self.device)
        self.model.eval()
        self.gnn_threshold = gnn_threshold

    def _build_nx_attack_graph(
        self,
        data:     Data,
        idx_to_id: dict[int, str],
        nodes:    list[dict[str, Any]],
    ) -> nx.DiGraph:
        """
        Run GNN inference and construct a weighted NetworkX DiGraph.

        Edge weight = CVSS-adjusted attack cost = (1 - attack_prob) × CVSS_inv
        Lower weight = easier / more likely lateral movement.
        """
        data = data.to(self.device)

        with torch.no_grad():
            node_embs = self.model.encode(data.x, data.edge_index)
            link_probs = self.model.predict_links(node_embs, data.edge_index)

        G = nx.DiGraph()

        # Add nodes with metadata
        id_to_node: dict[str, dict] = {n["asset_id"]: n for n in nodes}
        for idx, asset_id in idx_to_id.items():
            meta = id_to_node.get(asset_id, {})
            G.add_node(
                asset_id,
                tier=meta.get("tier", "unknown"),
                host=meta.get("host", "unknown"),
                hndl_score=float(meta.get("hndl_score", 5.0)),
                pqc_risk_score=float(meta.get("pqc_risk_score", 5.0)),
            )

        # Add edges above GNN threshold
        edge_index = data.edge_index.cpu().numpy()
        link_probs_np = link_probs.cpu().numpy()
        cvss_weights  = data.edge_attr.cpu().numpy() if data.edge_attr is not None else np.full(edge_index.shape[1], 5.0)

        for i in range(edge_index.shape[1]):
            src_idx = int(edge_index[0, i])
            dst_idx = int(edge_index[1, i])
            prob    = float(link_probs_np[i])
            cvss    = float(cvss_weights[i])

            if prob >= self.gnn_threshold:
                # Attack cost: lower CVSS & higher attack-prob = cheaper path
                cost = (1.0 - prob) * (10.0 - cvss + 0.001)
                G.add_edge(
                    idx_to_id[src_idx],
                    idx_to_id[dst_idx],
                    attack_prob=prob,
                    cvss=cvss,
                    cost=cost,
                )

        logger.info(
            "attack_graph_built",
            nodes=G.number_of_nodes(),
            edges=G.number_of_edges(),
            threshold=self.gnn_threshold,
        )
        return G

    def _enumerate_paths(
        self,
        G:          nx.DiGraph,
        source_id:  str,
        target_ids: list[str],
        k:          int,
    ) -> list[AttackPath]:
        """
        Use Yen's k-shortest paths (via NetworkX simple_paths) to enumerate
        lateral movement routes from source to each target, ordered by cost.
        """
        paths: list[AttackPath] = []
        path_id = 0

        for target_id in target_ids:
            if target_id not in G or source_id not in G:
                continue
            if not nx.has_path(G, source_id, target_id):
                continue

            try:
                # simple_paths returns by increasing length; weight gives cost order
                generator = nx.shortest_simple_paths(
                    G, source_id, target_id, weight="cost"
                )
                for raw_path in generator:
                    if path_id >= k:
                        break

                    # Reconstruct edge metadata
                    edge_types: list[str] = []
                    total_prob  = 1.0
                    total_cvss  = 0.0

                    for i in range(len(raw_path) - 1):
                        edge_data = G[raw_path[i]][raw_path[i + 1]]
                        edge_types.append(f"ATTACK(p={edge_data['attack_prob']:.2f})")
                        total_prob  *= edge_data["attack_prob"]
                        total_cvss  += edge_data["cvss"]

                    avg_cvss    = total_cvss / max(len(edge_types), 1)
                    total_risk  = sum(G.nodes[n].get("pqc_risk_score", 5.0) for n in raw_path)

                    path_nodes = [
                        AttackPathNode(
                            asset_id=nid,
                            host=G.nodes[nid].get("host", "unknown"),
                            tier=G.nodes[nid].get("tier", "unknown"),
                            pqc_risk_score=G.nodes[nid].get("pqc_risk_score"),
                        )
                        for nid in raw_path
                    ]

                    paths.append(AttackPath(
                        path_id=path_id,
                        nodes=path_nodes,
                        edge_types=edge_types,
                        cvss_score=min(10.0, avg_cvss),
                        total_risk=round(total_risk, 2),
                        hop_count=len(raw_path) - 1,
                        entry_node=raw_path[0],
                        target_node=raw_path[-1],
                        confidence=round(total_prob, 4),
                    ))
                    path_id += 1

            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue

        # Sort by combined risk: CVSS × (1-confidence) descending → most dangerous first
        paths.sort(key=lambda p: p.cvss_score * p.total_risk, reverse=True)
        # Re-assign path IDs after sort
        for i, p in enumerate(paths):
            p.path_id = i
        return paths

    def run(
        self,
        nodes:           list[dict[str, Any]],
        edges:           list[dict[str, Any]],
        source_asset_id: str,
        target_tier:     str = "database",
        k_paths:         int = 10,
        scan_id:         str | None = None,
    ) -> AttackPathReport:
        """
        Full inference pipeline: topology → GNN → attack graph → path enumeration.

        Args:
            nodes:           List of asset node dicts from Neo4j / DB.
            edges:           List of topology edge dicts.
            source_asset_id: Starting asset (typically an internet-facing node).
            target_tier:     Target tier label (default: 'database').
            k_paths:         Maximum number of attack paths to return.
            scan_id:         Optional scan run ID for traceability.

        Returns:
            AttackPathReport — sorted by risk (most critical first).
        """
        logger.info("attack_path_simulation_start", source=source_asset_id, k=k_paths)

        data, idx_to_id = build_pyg_graph(nodes, edges)
        G = self._build_nx_attack_graph(data, idx_to_id, nodes)

        # Find all target nodes matching the target tier
        target_ids = [
            nid for nid, attr in G.nodes(data=True)
            if attr.get("tier", "").lower().replace(" ", "") == target_tier.lower().replace(" ", "")
        ]

        if not target_ids:
            logger.warning("no_target_nodes_found", tier=target_tier)

        paths = self._enumerate_paths(G, source_asset_id, target_ids, k=k_paths)

        # Top-risk nodes: sorted by pqc_risk_score descending
        top_risk_nodes = sorted(
            [
                AttackPathNode(
                    asset_id=nid,
                    host=attr.get("host", "unknown"),
                    tier=attr.get("tier", "unknown"),
                    pqc_risk_score=attr.get("pqc_risk_score"),
                )
                for nid, attr in G.nodes(data=True)
            ],
            key=lambda n: n.pqc_risk_score or 0.0,
            reverse=True,
        )[:10]

        report = AttackPathReport(
            scan_id=scan_id or str(uuid.uuid4()),
            source_asset_id=uuid.UUID(source_asset_id) if source_asset_id else None,
            paths=paths,
            top_risk_nodes=top_risk_nodes,
        )

        logger.info(
            "attack_path_simulation_complete",
            paths_found=len(paths),
            top_risk=top_risk_nodes[0].asset_id if top_risk_nodes else None,
        )
        return report
