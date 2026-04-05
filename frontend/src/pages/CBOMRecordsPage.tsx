import React from 'react';

interface CBOMRecord {
  assetName: string;
  tlsVersion: string;
  cipher: string;
  keySize: string;
  keyExchange: string;
  sigAlgo: string;
  certExpiry: string;
  pqcReadiness: 'Ready' | 'At Risk' | 'PQC Native' | 'Critical';
}

const cbomRecords: CBOMRecord[] = [
  { assetName: 'Auth Service Proxy', tlsVersion: 'TLS 1.3', cipher: 'AES-256-GCM', keySize: '256-bit', keyExchange: 'ECDHE (X25519)', sigAlgo: 'RSA-PSS 4096', certExpiry: '2025-12-01', pqcReadiness: 'Ready' },
  { assetName: 'Payment Gateway API', tlsVersion: 'TLS 1.2', cipher: 'AES-128-CBC', keySize: '128-bit', keyExchange: 'DHE-RSA', sigAlgo: 'RSA-PKCS1v1.5', certExpiry: '2024-06-15', pqcReadiness: 'At Risk' },
  { assetName: 'Main Cluster DB-01', tlsVersion: 'TLS 1.3', cipher: 'ChaCha20-Poly1305', keySize: '256-bit', keyExchange: 'Hybrid (X25519 + Kyber)', sigAlgo: 'Ed25519', certExpiry: '2026-01-20', pqcReadiness: 'PQC Native' },
  { assetName: 'Legacy Inventory v1', tlsVersion: 'TLS 1.1', cipher: '3DES-EDE-CBC-SHA', keySize: '168-bit', keyExchange: 'RSA', sigAlgo: 'SHA-1', certExpiry: '2023-11-10', pqcReadiness: 'Critical' },
  { assetName: 'S3 Bucket Interface', tlsVersion: 'TLS 1.2', cipher: 'AES-256-SHA256', keySize: '256-bit', keyExchange: 'ECDHE-RSA', sigAlgo: 'ECDSA P-256', certExpiry: '2025-08-30', pqcReadiness: 'At Risk' },
  { assetName: 'Customer CRM Portal', tlsVersion: 'TLS 1.3', cipher: 'AES-128-GCM', keySize: '128-bit', keyExchange: 'ECDHE', sigAlgo: 'RSA-PSS', certExpiry: '2026-05-12', pqcReadiness: 'Ready' },
];

const CBOMRecordsPage: React.FC = () => {
  const getReadinessStyle = (status: CBOMRecord['pqcReadiness']) => {
    switch (status) {
      case 'Ready': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'At Risk': return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'PQC Native': return 'bg-teal-500/20 text-teal-400 border-teal-500/30';
      case 'Critical': return 'bg-red-500/10 text-red-500 border-red-500/20';
      default: return '';
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-background-light dark:bg-background-dark overflow-hidden font-display">
      {/* Page Header & Filters */}
      <div className="p-6 shrink-0 space-y-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Cryptographic Bill of Materials</h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm">Inventory and post-quantum readiness status for all enterprise cryptographic assets.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2 pt-2">
          <button className="flex items-center gap-2 px-3 py-1.5 bg-background-light dark:bg-slate-800 rounded text-xs font-medium border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors text-slate-900 dark:text-slate-300">
            <span>All Assets</span>
            <span className="material-symbols-outlined text-sm">expand_more</span>
          </button>
          <div className="h-4 w-px bg-slate-200 dark:bg-slate-700 mx-1"></div>
          <button className="flex items-center gap-2 px-3 py-1.5 bg-green-900/10 text-green-600 dark:text-green-400 rounded text-xs font-bold border border-green-900/20">
            <span className="material-symbols-outlined text-sm">check_circle</span>
            <span>PQC Ready</span>
          </button>
          <button className="flex items-center gap-2 px-3 py-1.5 bg-yellow-900/10 text-yellow-600 dark:text-yellow-400 rounded text-xs font-bold border border-yellow-900/20">
            <span className="material-symbols-outlined text-sm">warning</span>
            <span>At Risk</span>
          </button>
          <button className="flex items-center gap-2 px-3 py-1.5 bg-red-900/10 text-red-600 dark:text-red-400 rounded text-xs font-bold border border-red-900/20">
            <span className="material-symbols-outlined text-sm">error</span>
            <span>Critical</span>
          </button>
        </div>
      </div>

      {/* Table Container */}
      <div className="flex-1 px-6 pb-6 overflow-hidden">
        <div className="h-full flex flex-col border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden bg-white dark:bg-panel-dark shadow-sm">
          <div className="overflow-x-auto overflow-y-auto flex-1">
            <table className="w-full text-left border-collapse min-w-[1000px]">
              <thead className="sticky top-0 z-10 bg-slate-50 dark:bg-panel-dark shadow-[0_1px_0_0_rgba(203,213,225,1)] dark:shadow-[0_1px_0_0_rgba(36,54,71,1)]">
                <tr>
                  <th className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 border-r border-slate-200 dark:border-slate-800">Asset Name</th>
                  <th className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 border-r border-slate-200 dark:border-slate-800">TLS Version</th>
                  <th className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 border-r border-slate-200 dark:border-slate-800">Cipher</th>
                  <th className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 border-r border-slate-200 dark:border-slate-800">Key Size</th>
                  <th className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 border-r border-slate-200 dark:border-slate-800">Key Exchange</th>
                  <th className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 border-r border-slate-200 dark:border-slate-800">Sig Algorithm</th>
                  <th className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 border-r border-slate-200 dark:border-slate-800">Cert Expiry</th>
                  <th className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">PQC Readiness</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                {cbomRecords.map((record, i) => (
                  <tr key={i} className="hover:bg-primary/5 transition-colors group">
                    <td className="px-4 py-4 text-sm font-bold border-r border-slate-100 dark:border-slate-800">{record.assetName}</td>
                    <td className="px-4 py-4 text-sm border-r border-slate-100 dark:border-slate-800">
                      <span className={`px-2 py-0.5 rounded text-xs font-mono ${record.tlsVersion === 'TLS 1.1' ? 'bg-red-900/30 text-red-400' : 'bg-slate-100 dark:bg-slate-800'}`}>
                        {record.tlsVersion}
                      </span>
                    </td>
                    <td className={`px-4 py-4 text-sm font-mono border-r border-slate-100 dark:border-slate-800 uppercase ${record.tlsVersion === 'TLS 1.1' ? 'text-red-400/80' : 'text-slate-500 dark:text-slate-400'}`}>{record.cipher}</td>
                    <td className="px-4 py-4 text-sm font-bold border-r border-slate-100 dark:border-slate-800 text-slate-700 dark:text-slate-200">{record.keySize}</td>
                    <td className="px-4 py-4 text-sm border-r border-slate-100 dark:border-slate-800 text-slate-500 dark:text-slate-400">{record.keyExchange}</td>
                    <td className="px-4 py-4 text-sm border-r border-slate-100 dark:border-slate-800 text-slate-500 dark:text-slate-400">{record.sigAlgo}</td>
                    <td className="px-4 py-4 text-sm border-r border-slate-100 dark:border-slate-800 text-slate-500 dark:text-slate-400">{record.certExpiry}</td>
                    <td className="px-4 py-4 text-sm">
                      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border uppercase tracking-tighter ${getReadinessStyle(record.pqcReadiness)}`}>
                        {record.pqcReadiness}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {/* Table Footer / Pagination */}
          <div className="px-4 py-2 bg-slate-50 dark:bg-panel-dark border-t border-slate-200 dark:border-slate-800 flex items-center justify-between">
            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">SHOWING 1-6 OF 154 RECORDS</p>
            <div className="flex items-center gap-1 text-slate-500">
              <button className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded transition-colors disabled:opacity-30" disabled>
                <span className="material-symbols-outlined text-lg">first_page</span>
              </button>
              <button className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded transition-colors disabled:opacity-30" disabled>
                <span className="material-symbols-outlined text-lg">chevron_left</span>
              </button>
              <div className="px-3 flex items-center gap-1">
                <span className="text-xs font-bold bg-primary text-white px-2 py-0.5 rounded cursor-default">1</span>
                <span className="text-xs font-medium px-2 py-0.5 hover:bg-slate-200 dark:hover:bg-slate-700 rounded cursor-pointer transition-colors">2</span>
                <span className="text-xs font-medium px-2 py-0.5 hover:bg-slate-200 dark:hover:bg-slate-700 rounded cursor-pointer transition-colors">3</span>
              </div>
              <button className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded transition-colors">
                <span className="material-symbols-outlined text-lg">chevron_right</span>
              </button>
              <button className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded transition-colors">
                <span className="material-symbols-outlined text-lg">last_page</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CBOMRecordsPage;
