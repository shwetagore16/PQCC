import React, { useState } from 'react';

interface Asset {
  id: string;
  host: string;
  protocol: string;
  status: 'Secure' | 'Weak' | 'Expired' | 'PQC-Ready' | 'Non-Ready';
  tlsVersion: string;
  cipherSuite: string;
  keyAlgo: string;
  expiry: string;
  timestamp: string;
}

const mockAssets: Asset[] = [
  {
    id: 'AST-9021',
    host: '192.168.1.45',
    protocol: 'HTTPS / TLS 1.3',
    status: 'Secure',
    tlsVersion: 'TLS 1.3',
    cipherSuite: 'TLS_AES_256_GCM_SHA384',
    keyAlgo: 'ECDHE_RSA (3072 bits)',
    expiry: '2025-10-24',
    timestamp: '2024-03-20 14:22:10',
  },
  {
    id: 'AST-4432',
    host: '10.0.0.12',
    protocol: 'TLS 1.1 (Legacy)',
    status: 'Weak',
    tlsVersion: 'TLS 1.1',
    cipherSuite: 'TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA',
    keyAlgo: 'RSA (2048 bits)',
    expiry: '2024-12-15',
    timestamp: '2024-03-20 13:05:45',
  },
  {
    id: 'AST-1109',
    host: '172.16.5.4',
    protocol: 'SSL 3.0',
    status: 'Expired',
    tlsVersion: 'SSL 3.0',
    cipherSuite: 'SSL_RSA_WITH_RC4_128_MD5',
    keyAlgo: 'RSA (1024 bits)',
    expiry: '2023-11-20',
    timestamp: '2024-03-20 11:45:22',
  },
  {
    id: 'AST-8821',
    host: '192.168.1.90',
    protocol: 'Kyber Hybrid',
    status: 'PQC-Ready',
    tlsVersion: 'TLS 1.3 + Kyber768',
    cipherSuite: 'TLS_AES_256_GCM_SHA384',
    keyAlgo: 'ML-KEM-768 (Kyber)',
    expiry: '2026-05-12',
    timestamp: '2024-03-20 09:12:33',
  },
];

const ScanResultsPage: React.FC = () => {
  const [selectedAsset, setSelectedAsset] = useState<Asset>(mockAssets[0]);

  const getStatusColor = (status: Asset['status']) => {
    switch (status) {
      case 'Secure': return 'bg-green-500/20 text-green-500';
      case 'Weak': return 'bg-yellow-500/20 text-yellow-500';
      case 'Expired': return 'bg-red-500/20 text-red-500';
      case 'PQC-Ready': return 'bg-primary/20 text-primary';
      case 'Non-Ready': return 'bg-slate-500/20 text-slate-500';
      default: return 'bg-slate-500/20 text-slate-500';
    }
  };

  const getBadgeStyle = (status: Asset['status']) => {
    switch (status) {
      case 'Secure': return 'bg-green-500/10 border-green-500/30 text-green-600 dark:text-green-400';
      case 'Weak': return 'bg-yellow-500/10 border-yellow-500/30 text-yellow-600 dark:text-yellow-400';
      case 'Expired': return 'bg-red-500/10 border-red-500/30 text-red-600 dark:text-red-400';
      case 'PQC-Ready': return 'bg-primary/10 border-primary/30 text-primary';
      case 'Non-Ready': return 'bg-slate-500/10 border-slate-500/30 text-slate-600 dark:text-slate-400';
      default: return '';
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-8 space-y-6 bg-background-light dark:bg-background-dark">
      {/* Header with Title */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">Security Audit Results</h2>
      </div>

      {/* Status Badges Row */}
      <div className="flex flex-wrap gap-3">
        {[
          { label: 'Secure', icon: 'check_circle', status: 'Secure' as const },
          { label: 'Weak', icon: 'warning', status: 'Weak' as const },
          { label: 'Expired', icon: 'error', status: 'Expired' as const },
          { label: 'PQC-Ready', icon: 'computer', status: 'PQC-Ready' as const },
          { label: 'Non-Ready', icon: 'cancel', status: 'Non-Ready' as const },
        ].map((badge, i) => (
          <div key={i} className={`px-4 py-2 border rounded-lg flex items-center gap-2 text-xs font-bold uppercase tracking-wider ${getBadgeStyle(badge.status)}`}>
            <span className="material-symbols-outlined text-[16px]">{badge.icon}</span> {badge.label}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Results Table (2/3 width) */}
        <div className="xl:col-span-2 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden flex flex-col shadow-sm">
          <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center bg-slate-50 dark:bg-slate-800/50">
            <span className="font-bold text-sm">Asset Inventory</span>
            <button className="text-xs text-primary font-bold hover:underline">Refresh List</button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-950/50">
                <tr>
                  <th className="px-6 py-3 font-semibold">Asset ID</th>
                  <th className="px-6 py-3 font-semibold">Address</th>
                  <th className="px-6 py-3 font-semibold">Protocol</th>
                  <th className="px-6 py-3 font-semibold text-center">Security Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {mockAssets.map((asset) => (
                  <tr 
                    key={asset.id} 
                    onClick={() => setSelectedAsset(asset)}
                    className={`hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors cursor-pointer ${selectedAsset.id === asset.id ? 'bg-primary/5 dark:bg-primary/10 border-l-4 border-l-primary' : ''}`}
                  >
                    <td className="px-6 py-4 font-medium text-slate-700 dark:text-slate-300">{asset.id}</td>
                    <td className="px-6 py-4 font-mono text-slate-500">{asset.host}</td>
                    <td className="px-6 py-4 text-slate-600 dark:text-slate-400">{asset.protocol}</td>
                    <td className="px-6 py-4 text-center">
                      <span className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase ${getStatusColor(asset.status)}`}>
                        {asset.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Selected Result Card (1/3 width) */}
        <div className="xl:col-span-1 flex flex-col gap-6">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xl overflow-hidden">
            <div className="px-6 py-4 bg-primary text-white flex justify-between items-center">
              <h3 className="font-bold text-sm">Asset Detailed Analysis</h3>
              <span className="material-symbols-outlined text-[18px]">info</span>
            </div>
            <div className="p-6 space-y-4">
              <div className="space-y-1">
                <label className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Asset ID</label>
                <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">{selectedAsset.id}</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">TLS Version</label>
                  <p className="text-sm text-slate-700 dark:text-slate-300">{selectedAsset.tlsVersion}</p>
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Cert Status</label>
                  <p className={`text-sm font-medium ${selectedAsset.status === 'Expired' ? 'text-red-500' : 'text-green-500'}`}>
                    {selectedAsset.status === 'Expired' ? 'Expired' : 'Active / Valid'}
                  </p>
                </div>
              </div>
              <div className="space-y-1">
                <label className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Cipher Suite</label>
                <p className="text-xs font-mono bg-slate-100 dark:bg-slate-800 p-2 rounded border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400">
                  {selectedAsset.cipherSuite}
                </p>
              </div>
              <div className="space-y-1">
                <label className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Key Algorithm</label>
                <p className="text-sm text-slate-700 dark:text-slate-300">{selectedAsset.keyAlgo}</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Expiry</label>
                  <p className="text-sm text-slate-700 dark:text-slate-300">{selectedAsset.expiry}</p>
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Timestamp</label>
                  <p className="text-[11px] text-slate-500">{selectedAsset.timestamp}</p>
                </div>
              </div>
              <div className="pt-4 flex flex-col gap-2">
                <button className="w-full py-2 bg-primary/10 hover:bg-primary/20 text-primary font-bold text-xs rounded-lg transition-all border border-primary/20 flex items-center justify-center gap-2">
                  <span className="material-symbols-outlined text-[18px]">download</span>
                  Export Result
                </button>
                <button className="w-full py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-400 font-bold text-xs rounded-lg transition-all flex items-center justify-center gap-2">
                  <span className="material-symbols-outlined text-[18px]">history</span>
                  View History
                </button>
              </div>
            </div>
          </div>
          {/* Scan Metadata */}
          <div className="bg-primary/5 rounded-xl border border-primary/20 p-4">
            <div className="flex items-center gap-3 mb-3">
              <span className="material-symbols-outlined text-primary">analytics</span>
              <h4 className="text-sm font-bold text-primary">Scan Context</h4>
            </div>
            <p className="text-xs leading-relaxed text-slate-600 dark:text-slate-300">
              This asset was scanned as part of the <span className="font-bold text-primary">Quantum-Ready Audit</span>. No critical vulnerabilities were detected, however, cipher rotation is recommended every 12 months.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScanResultsPage;
