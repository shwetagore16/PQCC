import React, { useState, useMemo } from 'react';

interface Asset {
  id: string;
  name: string;
  type: string;
  domain: string;
  owner: string;
  status: 'Active' | 'Pending' | 'Offline';
  pqcStatus: 'Ready' | 'Not Ready';
  riskScore: number;
  lastScan: string;
}

interface AssetConnection {
  from: string;
  to: string;
}

const initialAssets: Asset[] = [
  { id: '#AST-4821', name: 'API Gateway Prod', type: 'API', domain: 'api.prod.enterprise.com', owner: 'Alex Rivera', status: 'Active', pqcStatus: 'Not Ready', riskScore: 8.4, lastScan: '2h ago' },
  { id: '#AST-5902', name: 'Customer Portal', type: 'Domain', domain: 'portal.enterprise.com', owner: 'Sarah Chen', status: 'Active', pqcStatus: 'Ready', riskScore: 1.2, lastScan: 'Yesterday' },
  { id: '#AST-1138', name: 'Main Database Node', type: 'Server', domain: '10.0.42.112', owner: 'Infra Team', status: 'Pending', pqcStatus: 'Not Ready', riskScore: 9.1, lastScan: 'Never' },
  { id: '#AST-8821', name: 'Marketing Site', type: 'Domain', domain: 'marketing.enterprise.com', owner: 'Marketing Div', status: 'Offline', pqcStatus: 'Not Ready', riskScore: 4.5, lastScan: '3d ago' },
];

const assetConnections: AssetConnection[] = [
  { from: '#AST-4821', to: '#AST-1138' },
  { from: '#AST-5902', to: '#AST-1138' },
  { from: '#AST-4821', to: '#AST-5902' },
  { from: '#AST-8821', to: '#AST-5902' },
];

interface NodePosition {
  x: number;
  y: number;
}

const TopologicalAssetView: React.FC<{ assets: Asset[]; connections: AssetConnection[] }> = ({ assets, connections }) => {
  const positions = useMemo(() => {
    const pos: { [key: string]: NodePosition } = {};
    const centerX = 400;
    const centerY = 300;
    const radius = 150;

    // Position nodes in a circle with some variation
    assets.forEach((asset, index) => {
      const angle = (index / assets.length) * 2 * Math.PI;
      pos[asset.id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      };
    });

    return pos;
  }, [assets]);

  const getRiskColor = (score: number) => {
    if (score < 4) return '#10b981';
    if (score < 7) return '#f59e0b';
    return '#ef4444';
  };

  const getStatusColor = (status: string) => {
    if (status === 'Active') return '#06b6d4';
    if (status === 'Pending') return '#eab308';
    return '#6b7280';
  };

  return (
    <div className="flex-1 flex flex-col p-8 overflow-auto bg-background-light dark:bg-background-dark">
      <h2 className="text-2xl font-bold mb-6 text-slate-900 dark:text-slate-100">Asset Topology</h2>
      
      <div className="flex-1 bg-white dark:bg-primary/5 rounded-xl border border-slate-200 dark:border-primary/20 overflow-hidden shadow-sm">
        <svg className="w-full h-full" viewBox="0 0 800 600">
          {/* Draw connections */}
          {connections.map((conn, idx) => {
            const fromPos = positions[conn.from];
            const toPos = positions[conn.to];
            if (fromPos && toPos) {
              return (
                <line
                  key={`conn-${idx}`}
                  x1={fromPos.x}
                  y1={fromPos.y}
                  x2={toPos.x}
                  y2={toPos.y}
                  stroke="#cbd5e1"
                  strokeWidth="2"
                  markerEnd="url(#arrowhead)"
                  className="dark:stroke-primary/30"
                />
              );
            }
            return null;
          })}

          {/* Arrow marker definition */}
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="10"
              refX="9"
              refY="3"
              orient="auto"
            >
              <polygon points="0 0, 10 3, 0 6" fill="#cbd5e1" className="dark:fill-primary/30" />
            </marker>
          </defs>

          {/* Draw asset nodes */}
          {assets.map((asset) => {
            const pos = positions[asset.id];
            if (!pos) return null;

            return (
              <g key={asset.id}>
                {/* Node circle */}
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r="45"
                  fill={getRiskColor(asset.riskScore)}
                  opacity="0.2"
                  stroke={getRiskColor(asset.riskScore)}
                  strokeWidth="2"
                />

                {/* Status indicator ring */}
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r="40"
                  fill="none"
                  stroke={getStatusColor(asset.status)}
                  strokeWidth="3"
                  opacity="0.8"
                />

                {/* Node center */}
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r="32"
                  fill="white"
                  className="dark:fill-primary/10"
                  stroke={getRiskColor(asset.riskScore)}
                  strokeWidth="2"
                />

                {/* Asset type icon background */}
                <rect
                  x={pos.x - 10}
                  y={pos.y - 28}
                  width="20"
                  height="20"
                  rx="3"
                  fill={getRiskColor(asset.riskScore)}
                />

                {/* Asset type text */}
                <text
                  x={pos.x}
                  y={pos.y - 13}
                  textAnchor="middle"
                  fontSize="10"
                  fontWeight="bold"
                  fill="white"
                >
                  {asset.type.charAt(0)}
                </text>

                {/* Asset name */}
                <text
                  x={pos.x}
                  y={pos.y + 5}
                  textAnchor="middle"
                  fontSize="11"
                  fontWeight="bold"
                  className="fill-slate-900 dark:fill-slate-100"
                >
                  {asset.name.split(' ').slice(0, 2).join(' ')}
                </text>

                {/* Risk score */}
                <text
                  x={pos.x}
                  y={pos.y + 20}
                  textAnchor="middle"
                  fontSize="9"
                  fontWeight="bold"
                  fill={getRiskColor(asset.riskScore)}
                >
                  Risk: {asset.riskScore.toFixed(1)}
                </text>

                {/* Tooltip info on hover */}
                <title>{`${asset.name}\nType: ${asset.type}\nStatus: ${asset.status}\nRisk: ${asset.riskScore.toFixed(1)}\nPQC: ${asset.pqcStatus}`}</title>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Legend */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
          <span className="text-slate-600 dark:text-slate-400">Low Risk</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-amber-500"></div>
          <span className="text-slate-600 dark:text-slate-400">Medium Risk</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <span className="text-slate-600 dark:text-slate-400">High Risk</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full border-2 border-cyan-500"></div>
          <span className="text-slate-600 dark:text-slate-400">Active</span>
        </div>
      </div>
    </div>
  );
};

const AssetManagementPage: React.FC = () => {
  const [assets] = useState<Asset[]>(initialAssets);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [viewMode, setViewMode] = useState<'table' | 'topological'>('table');

  const getRiskColor = (score: number) => {
    if (score < 4) return 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20';
    if (score < 7) return 'text-amber-500 bg-amber-500/10 border-amber-500/20';
    return 'text-red-500 bg-red-500/10 border-red-500/20';
  };

  return (
    <div className="flex-1 flex flex-col p-8 overflow-y-auto bg-background-light dark:bg-background-dark">
      {/* Table Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-8 text-slate-900 dark:text-slate-100">
        <div className="flex items-center gap-4">
          <h1 className="text-3xl font-black tracking-tight">Assets</h1>
          <span className="px-3 py-1 rounded bg-primary/10 text-primary text-xs font-bold uppercase tracking-wider">128 Total</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-100 dark:bg-primary/10 rounded-lg p-1">
            <button 
              onClick={() => setViewMode('table')}
              className={`flex items-center gap-2 px-4 py-2 rounded font-bold text-sm transition-colors ${
                viewMode === 'table' 
                  ? 'bg-white dark:bg-primary/20 text-primary shadow-sm' 
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              <span className="material-symbols-outlined text-lg">table_chart</span>
              Table
            </button>
            <button 
              onClick={() => setViewMode('topological')}
              className={`flex items-center gap-2 px-4 py-2 rounded font-bold text-sm transition-colors ${
                viewMode === 'topological' 
                  ? 'bg-white dark:bg-primary/20 text-primary shadow-sm' 
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              <span className="material-symbols-outlined text-lg">share</span>
              Topology
            </button>
          </div>
          <button className="flex items-center gap-2 px-4 py-2 border border-slate-200 dark:border-primary/30 rounded font-bold text-sm hover:bg-slate-50 dark:hover:bg-primary/10 transition-colors">
            <span className="material-symbols-outlined text-lg">filter_list</span>
            Filter View
          </button>
          <button 
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 px-6 py-2 bg-primary text-white rounded font-bold text-sm shadow-lg shadow-primary/30 hover:brightness-110 active:scale-95 transition-all"
          >
            <span className="material-symbols-outlined text-lg">add_circle</span>
            Add New Asset
          </button>
        </div>
      </div>

      {/* Conditional View Rendering */}
      {viewMode === 'table' ? (
      <div className="bg-white dark:bg-primary/5 rounded-xl border border-slate-200 dark:border-primary/20 overflow-hidden shadow-sm">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 dark:bg-primary/10 border-b border-slate-200 dark:border-primary/20">
              <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">ID</th>
              <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Name</th>
              <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Type</th>
              <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">PQC Status</th>
              <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Risk Score</th>
              <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Domain / IP</th>
              <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Status</th>
              <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Last Scan</th>
              <th className="px-6 py-4"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-primary/10 text-slate-700 dark:text-slate-300">
            {assets.map((asset) => (
              <tr key={asset.id} className="hover:bg-slate-50 dark:hover:bg-primary/5 transition-colors group">
                <td className="px-6 py-4 text-sm font-mono text-slate-400">{asset.id}</td>
                <td className="px-6 py-4 text-sm font-bold">{asset.name}</td>
                <td className="px-6 py-4 text-sm">{asset.type}</td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 rounded text-[10px] font-black uppercase tracking-tighter border ${asset.pqcStatus === 'Ready' ? 'bg-teal-500/20 text-teal-400 border-teal-500/30' : 'bg-red-500/20 text-red-400 border-red-500/30'}`}>
                    {asset.pqcStatus}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getRiskColor(asset.riskScore)}`}>
                    {asset.riskScore.toFixed(1)}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-400">{asset.domain}</td>
                <td className="px-6 py-4 text-sm">{asset.status}</td>
                <td className="px-6 py-4 text-sm text-slate-500">{asset.lastScan}</td>
                <td className="px-6 py-4 text-right">
                  <button className="p-1.5 opacity-0 group-hover:opacity-100 hover:bg-slate-200 dark:hover:bg-primary/20 rounded">
                    <span className="material-symbols-outlined text-lg">more_vert</span>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Table Footer/Pagination */}
        <div className="px-6 py-4 border-t border-slate-200 dark:border-primary/20 bg-slate-50 dark:bg-primary/5 flex items-center justify-between">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">Page 1 of 8</span>
          <div className="flex gap-1">
            <button className="px-3 py-1 border border-slate-200 dark:border-primary/30 rounded text-sm hover:bg-white dark:hover:bg-primary/10 disabled:opacity-50" disabled>Previous</button>
            <button className="px-3 py-1 bg-primary text-white rounded text-sm font-bold">1</button>
            <button className="px-3 py-1 border border-slate-200 dark:border-primary/30 rounded text-sm hover:bg-white dark:hover:bg-primary/10">2</button>
            <button className="px-3 py-1 border border-slate-200 dark:border-primary/30 rounded text-sm hover:bg-white dark:hover:bg-primary/10">3</button>
            <button className="px-3 py-1 border border-slate-200 dark:border-primary/30 rounded text-sm hover:bg-white dark:hover:bg-primary/10">Next</button>
          </div>
        </div>
      </div>
      ) : (
        <TopologicalAssetView assets={assets} connections={assetConnections} />
      )}

      {/* Modal Dialog */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-background-dark/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-xl bg-white dark:bg-background-dark border border-slate-200 dark:border-primary/30 rounded-xl shadow-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 dark:border-primary/20 flex items-center justify-between bg-slate-50 dark:bg-primary/5">
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">Add New Asset</h3>
              <button 
                onClick={() => setIsModalOpen(false)}
                className="p-1 hover:bg-slate-200 dark:hover:bg-primary/20 rounded text-slate-500"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            <div className="p-8 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="md:col-span-2">
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Asset Name</label>
                  <input className="w-full px-4 py-2.5 rounded bg-slate-50 dark:bg-primary/10 border border-slate-200 dark:border-primary/20 focus:ring-primary focus:border-primary outline-none text-sm text-slate-900 dark:text-slate-100" placeholder="e.g. Production Load Balancer" type="text"/>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Asset Type</label>
                  <select className="w-full px-4 py-2.5 rounded bg-slate-50 dark:bg-primary/10 border border-slate-200 dark:border-primary/20 focus:ring-primary focus:border-primary outline-none text-sm text-slate-900 dark:text-slate-100">
                    <option>Domain</option>
                    <option>API</option>
                    <option>Server</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Domain / IP Address</label>
                  <input className="w-full px-4 py-2.5 rounded bg-slate-50 dark:bg-primary/10 border border-slate-200 dark:border-primary/20 focus:ring-primary focus:border-primary outline-none text-sm text-slate-900 dark:text-slate-100" placeholder="192.168.1.1" type="text"/>
                </div>
                <div className="md:col-span-2">
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Description</label>
                  <textarea className="w-full px-4 py-2.5 rounded bg-slate-50 dark:bg-primary/10 border border-slate-200 dark:border-primary/20 focus:ring-primary focus:border-primary outline-none text-sm text-slate-900 dark:text-slate-100" placeholder="Additional details about this asset..." rows={3}></textarea>
                </div>
              </div>
            </div>
            <div className="px-8 py-6 bg-slate-50 dark:bg-primary/5 border-t border-slate-100 dark:border-primary/20 flex justify-end gap-3">
              <button 
                onClick={() => setIsModalOpen(false)}
                className="px-6 py-2 border border-slate-200 dark:border-primary/30 rounded font-bold text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-primary/10 transition-colors"
              >
                Cancel
              </button>
              <button 
                onClick={() => setIsModalOpen(false)}
                className="px-6 py-2 bg-primary text-white rounded font-bold text-sm shadow-lg shadow-primary/30 hover:brightness-110 active:scale-95 transition-all"
              >
                Create Asset
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AssetManagementPage;
