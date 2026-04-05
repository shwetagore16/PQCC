// frontend/src/components/visualizations/RiskHeatmap.tsx
//
// PQC Risk Heatmap — D3.js treemap where:
//   • Cell SIZE    = HNDL score (higher risk → larger cell)
//   • Cell COLOR   = RiskBand (red / orange / yellow / green)
//   • Drill-down   = Click a tier cell to zoom into its asset children
//
// Implementation uses d3.treemap() with squarify layout.
// The component manages its own D3 lifecycle via useRef + useEffect
// and avoids React/D3 DOM conflicts by letting D3 own the <svg> exclusively.

import * as d3 from "d3";
import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import type { HeatmapNode, RiskBand } from "../../types";

// ── Color palette ─────────────────────────────────────────────────────────────
const BAND_COLORS: Record<RiskBand, string> = {
  critical: "#ef4444",   // red-500
  high:     "#f97316",   // orange-500
  medium:   "#eab308",   // yellow-500
  low:      "#22c55e",   // green-500
};

const BAND_TEXT: Record<RiskBand, string> = {
  critical: "#ffffff",
  high:     "#ffffff",
  medium:   "#111827",
  low:      "#ffffff",
};

// ── Component Props ───────────────────────────────────────────────────────────
interface RiskHeatmapProps {
  /** Hierarchical asset data. Root node should have children grouped by tier. */
  data:       HeatmapNode;
  width?:     number;
  height?:    number;
  /** Called when user drills down into a specific asset cell. */
  onAssetClick?: (node: HeatmapNode) => void;
}

// ── React Component ───────────────────────────────────────────────────────────
export default function RiskHeatmap({
  data,
  width  = 960,
  height = 560,
  onAssetClick,
}: RiskHeatmapProps) {
  const svgRef            = useRef<SVGSVGElement>(null);
  const [drillPath, setDrillPath] = useState<HeatmapNode[]>([data]);   // Breadcrumb stack
  const [tooltip, setTooltip]     = useState<{ x: number; y: number; node: HeatmapNode } | null>(null);
  const [animKey, setAnimKey]     = useState(0); // Force D3 re-render on drill

  // Current "root" at the current drill depth
  const currentRoot = drillPath[drillPath.length - 1];

  // ── Build D3 hierarchy from current root ───────────────────────────────────
  const hierarchy = useMemo(() => {
    return d3
      .hierarchy<HeatmapNode>(currentRoot)
      .sum((d) => (d.children ? 0 : Math.max(0.1, d.hndl_score)))
      .sort((a, b) => (b.value ?? 0) - (a.value ?? 0));
  }, [currentRoot]);

  // ── D3 treemap layout ──────────────────────────────────────────────────────
  const treemap = useMemo(
    () =>
      d3
        .treemap<HeatmapNode>()
        .size([width, height])
        .paddingOuter(6)
        .paddingInner(3)
        .paddingTop(20)
        .round(true)
        .tile(d3.treemapSquarify),
    [width, height]
  );

  // ── Draw / update SVG ──────────────────────────────────────────────────────
  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();   // Full re-render on each update

    const root = treemap(hierarchy);

    // ── Leaf cells ──────────────────────────────────────────────────────────
    const cells = svg
      .selectAll<SVGGElement, d3.HierarchyRectangularNode<HeatmapNode>>("g.cell")
      .data(root.leaves())
      .join("g")
      .attr("class", "cell")
      .attr("transform", (d) => `translate(${d.x0},${d.y0})`)
      .style("cursor", "pointer");

    // Background rect
    cells
      .append("rect")
      .attr("width",  (d) => Math.max(0, d.x1 - d.x0))
      .attr("height", (d) => Math.max(0, d.y1 - d.y0))
      .attr("rx", 4)
      .attr("fill", (d) => BAND_COLORS[d.data.risk_band])
      .attr("fill-opacity", 0.88)
      .attr("stroke", "#0f172a")
      .attr("stroke-width", 1)
      // Entrance animation
      .attr("opacity", 0)
      .transition()
      .duration(400)
      .attr("opacity", 1);

    // HNDL score heatmap overlay (darken centre for high scores)
    cells
      .append("rect")
      .attr("width",  (d) => Math.max(0, d.x1 - d.x0))
      .attr("height", (d) => Math.max(0, d.y1 - d.y0))
      .attr("rx", 4)
      .attr("fill", (d) => `rgba(0,0,0,${(d.data.hndl_score / 10) * 0.25})`)
      .attr("pointer-events", "none");

    // Host label (only if cell is large enough)
    cells
      .filter((d) => d.x1 - d.x0 > 60 && d.y1 - d.y0 > 30)
      .append("text")
      .attr("x", 6)
      .attr("y", 16)
      .attr("fill", (d) => BAND_TEXT[d.data.risk_band])
      .attr("font-size", (d) => Math.min(13, Math.max(9, (d.x1 - d.x0) / 10)) + "px")
      .attr("font-family", "Inter, ui-sans-serif, system-ui")
      .attr("font-weight", "600")
      .text((d) => d.data.host.slice(0, 20))
      .attr("clip-path", (d, i) => `url(#clip-${i})`);

    // HNDL score number
    cells
      .filter((d) => d.x1 - d.x0 > 40 && d.y1 - d.y0 > 44)
      .append("text")
      .attr("x", 6)
      .attr("y", 30)
      .attr("fill", (d) => BAND_TEXT[d.data.risk_band])
      .attr("fill-opacity", 0.75)
      .attr("font-size", "10px")
      .attr("font-family", "Inter, ui-sans-serif, system-ui")
      .text((d) => `HNDL ${d.data.hndl_score.toFixed(1)}`);

    // Clip paths to prevent text overflow
    cells
      .append("clipPath")
      .attr("id", (_, i) => `clip-${i}`)
      .append("rect")
      .attr("width",  (d) => Math.max(0, d.x1 - d.x0 - 4))
      .attr("height", (d) => Math.max(0, d.y1 - d.y0 - 4));

    // ── Parent group headers ─────────────────────────────────────────────────
    const parents = svg
      .selectAll<SVGGElement, d3.HierarchyRectangularNode<HeatmapNode>>("g.parent")
      .data(root.descendants().filter((d) => d.depth === 1))
      .join("g")
      .attr("class", "parent")
      .attr("transform", (d) => `translate(${d.x0},${d.y0})`);

    parents
      .append("text")
      .attr("x", 4)
      .attr("y", 14)
      .attr("fill", "#94a3b8")
      .attr("font-size", "11px")
      .attr("font-weight", "700")
      .attr("text-transform", "uppercase")
      .attr("font-family", "Inter, ui-sans-serif, system-ui")
      .text((d) => d.data.tier.toUpperCase());

    // ── Interactions ─────────────────────────────────────────────────────────

    // Hover tooltip trigger
    cells
      .on("mouseenter", (event: MouseEvent, d) => {
        setTooltip({
          x: event.clientX,
          y: event.clientY,
          node: d.data,
        });
      })
      .on("mousemove", (event: MouseEvent) => {
        setTooltip((prev) => prev ? { ...prev, x: event.clientX, y: event.clientY } : null);
      })
      .on("mouseleave", () => setTooltip(null));

    // Click — drill down if has children, else fire onAssetClick
    cells.on("click", (_: MouseEvent, d) => {
      if (d.data.children && d.data.children.length > 0) {
        setDrillPath((prev) => [...prev, d.data]);
        setAnimKey((k) => k + 1);
      } else {
        onAssetClick?.(d.data);
      }
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hierarchy, treemap, animKey]);

  // ── Breadcrumb navigation ──────────────────────────────────────────────────
  const handleBreadcrumb = useCallback((idx: number) => {
    setDrillPath((prev) => prev.slice(0, idx + 1));
    setAnimKey((k) => k + 1);
  }, []);

  return (
    <div className="flex flex-col w-full bg-gray-900 rounded-2xl border border-gray-800 overflow-hidden">
      {/* Title + Legend */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-gray-800">
        <span className="text-sm font-bold text-white">📊 PQC Risk Heatmap</span>
        <div className="flex items-center gap-3 text-xs">
          {(Object.entries(BAND_COLORS) as [RiskBand, string][]).map(([band, color]) => (
            <span key={band} className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-sm" style={{ background: color }} />
              <span className="text-gray-400 capitalize">{band}</span>
            </span>
          ))}
          <span className="text-gray-600">| Size = HNDL score</span>
        </div>
      </div>

      {/* Breadcrumbs */}
      {drillPath.length > 1 && (
        <div className="flex items-center gap-1 px-5 py-2 bg-gray-800/50 text-xs text-gray-400">
          {drillPath.map((node, idx) => (
            <React.Fragment key={idx}>
              <button
                className="hover:text-cyan-400 transition"
                onClick={() => handleBreadcrumb(idx)}
              >
                {idx === 0 ? "🏠 All" : node.host}
              </button>
              {idx < drillPath.length - 1 && <span className="text-gray-600">/</span>}
            </React.Fragment>
          ))}
        </div>
      )}

      {/* D3 SVG Canvas */}
      <div className="overflow-hidden">
        <svg
          ref={svgRef}
          width={width}
          height={height}
          viewBox={`0 0 ${width} ${height}`}
          className="w-full"
          style={{ maxHeight: height }}
        />
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div
          className="fixed z-50 pointer-events-none bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 shadow-2xl text-xs"
          style={{ left: tooltip.x + 14, top: tooltip.y - 10 }}
        >
          <p className="font-bold text-white mb-1">{tooltip.node.host}</p>
          <p className="text-gray-400">Tier: <span className="text-cyan-300">{tooltip.node.tier}</span></p>
          <p className="text-gray-400">
            HNDL: <span style={{ color: BAND_COLORS[tooltip.node.risk_band] }} className="font-bold">
              {tooltip.node.hndl_score.toFixed(2)}
            </span>
          </p>
          <p className="text-gray-400">
            Risk: <span className="capitalize font-semibold" style={{ color: BAND_COLORS[tooltip.node.risk_band] }}>
              {tooltip.node.risk_band}
            </span>
          </p>
          {tooltip.node.quantum_label && (
            <p className="text-gray-400 mt-1">
              Label: <span className="text-yellow-300">
                {tooltip.node.quantum_label.replace(/_/g, " ")}
              </span>
            </p>
          )}
          {tooltip.node.children && (
            <p className="text-gray-500 mt-1">🔍 Click to drill down</p>
          )}
        </div>
      )}
    </div>
  );
}
