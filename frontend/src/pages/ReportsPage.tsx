import React from 'react';

const ReportsPage: React.FC = () => {
  return (
    <div className="flex-1 overflow-y-auto bg-slate-100 dark:bg-background-dark p-6 font-display">
      <div className="max-w-6xl mx-auto flex flex-col gap-6">
        <div className="flex items-end justify-between">
          <div className="text-slate-900 dark:text-slate-100">
            <h1 className="text-2xl font-bold">Generate Reports</h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm">Configure parameters and export system documentation</p>
          </div>
          <div className="flex gap-2">
            <button className="flex items-center gap-2 px-4 py-2 rounded bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors">
              <span className="material-symbols-outlined text-base">history</span>
              History
            </button>
            <button className="flex items-center gap-2 px-4 py-2 rounded bg-primary text-white text-sm font-bold shadow-lg shadow-primary/20 hover:bg-primary/90">
              <span className="material-symbols-outlined text-base">play_arrow</span>
              Run Batch
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Configuration Panel */}
          <div className="lg:col-span-5 flex flex-col gap-6">
            <div className="bg-white dark:bg-slate-900 p-5 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm">
              <h3 className="text-sm font-bold mb-4 flex items-center gap-2 uppercase tracking-wide opacity-80 text-slate-900 dark:text-slate-100">
                <span className="material-symbols-outlined text-primary text-lg">tune</span>
                Report Parameters
              </h3>
              <div className="space-y-4">
                {/* Report Types */}
                <div>
                  <label className="text-xs font-bold text-slate-500 mb-2 block tracking-wider">REPORT TYPE</label>
                  <div className="grid grid-cols-1 gap-2">
                    {[
                      { title: 'Asset Summary', desc: 'Inventory and lifecycle overview' },
                      { title: 'Scan Results', desc: 'Technical vulnerability findings' },
                      { title: 'CBOM', desc: 'Component Bill of Materials (SBOM-compliant)' },
                      { title: 'Risk Assessment', desc: 'Prioritized threats and scoring' },
                      { title: 'PQC Status', desc: 'Post-Quantum Cryptography readiness' },
                    ].map((type, i) => (
                      <label key={i} className={`flex items-center gap-3 p-3 rounded border border-slate-200 dark:border-slate-800 ${i === 0 ? 'bg-slate-50 dark:bg-slate-800/50 border-primary/50' : ''} cursor-pointer hover:border-primary/50 transition-colors`}>
                        <input defaultChecked={i === 0} className="text-primary focus:ring-primary h-4 w-4" name="report_type" type="radio"/>
                        <div className="flex-1">
                          <p className="text-sm font-bold text-slate-900 dark:text-slate-100">{type.title}</p>
                          <p className="text-[11px] text-slate-500 dark:text-slate-400 opacity-60">{type.desc}</p>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
                {/* Date Selector */}
                <div>
                  <label className="text-xs font-bold text-slate-500 mb-2 block uppercase tracking-wider">Time Range</label>
                  <select className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded p-2.5 text-sm focus:ring-1 focus:ring-primary outline-none text-slate-900 dark:text-slate-100">
                    <option>Last 24 Hours</option>
                    <option defaultValue="Last 7 Days">Last 7 Days</option>
                    <option>Last 30 Days</option>
                    <option>Custom Range...</option>
                  </select>
                </div>
                <button className="w-full bg-primary hover:bg-primary/90 text-white font-bold py-3 rounded mt-2 transition-all flex items-center justify-center gap-2">
                  <span className="material-symbols-outlined">refresh</span>
                  Generate Preview
                </button>
              </div>
            </div>
          </div>

          {/* Preview & Export Panel */}
          <div className="lg:col-span-7 flex flex-col gap-4">
            {/* Toolbar */}
            <div className="bg-white dark:bg-slate-900 p-3 rounded-lg border border-slate-200 dark:border-slate-800 flex items-center justify-between shadow-sm">
              <div className="flex items-center gap-4 text-slate-900 dark:text-slate-100">
                <h3 className="text-sm font-bold px-2 tracking-wider">PREVIEW</h3>
                <div className="h-4 w-px bg-slate-200 dark:bg-slate-700"></div>
                <div className="flex items-center gap-1">
                  <button className="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded">
                    <span className="material-symbols-outlined text-lg">zoom_out</span>
                  </button>
                  <span className="text-xs font-medium px-2">100%</span>
                  <button className="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded">
                    <span className="material-symbols-outlined text-lg">zoom_in</span>
                  </button>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold opacity-40 mr-2 uppercase text-slate-500">Export as</span>
                <button className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 text-xs font-bold hover:bg-red-500/20">
                  <span className="material-symbols-outlined text-sm">picture_as_pdf</span>
                  PDF
                </button>
                <button className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 text-xs font-bold hover:bg-emerald-500/20">
                  <span className="material-symbols-outlined text-sm">csv</span>
                  CSV
                </button>
              </div>
            </div>
            {/* Preview Surface */}
            <div className="flex-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden min-h-[500px] flex flex-col shadow-sm">
              <div className="p-8 space-y-8 flex-1 overflow-y-auto">
                <div className="flex justify-between items-start border-b border-slate-100 dark:border-slate-800 pb-6">
                  <div>
                    <h2 className="text-xl font-bold uppercase tracking-tighter text-slate-900 dark:text-slate-100">Asset Summary Report</h2>
                    <p className="text-xs text-slate-500 mt-1">Generated on May 24, 2024 at 14:32:01 UTC</p>
                  </div>
                  <div className="text-right">
                    <div className="text-primary font-bold text-sm">SEC-2024-0524-A</div>
                    <div className="text-[10px] uppercase font-bold opacity-40 text-slate-500">Classification: Internal</div>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-6">
                  <div className="p-4 rounded border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/30">
                    <p className="text-[10px] font-bold text-slate-500 uppercase">Total Assets</p>
                    <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">1,422</p>
                    <p className="text-[10px] text-emerald-500 mt-1">+12 since last week</p>
                  </div>
                  <div className="p-4 rounded border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/30">
                    <p className="text-[10px] font-bold text-slate-500 uppercase">Risk Level</p>
                    <p className="text-2xl font-bold text-amber-500">Medium</p>
                    <p className="text-[10px] text-slate-500 mt-1">CVSS Average: 4.8</p>
                  </div>
                  <div className="p-4 rounded border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/30">
                    <p className="text-[10px] font-bold text-slate-500 uppercase">Scanned</p>
                    <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">98.2%</p>
                    <p className="text-[10px] text-slate-500 mt-1">24 assets pending</p>
                  </div>
                </div>
                <div>
                  <h4 className="text-xs font-bold mb-4 uppercase text-slate-500 tracking-wide">Infrastructure Breakdown</h4>
                  <div className="space-y-3">
                    {[
                      { label: 'Cloud Infrastructure (AWS/Azure)', value: '642', width: '45%' },
                      { label: 'On-Premise Servers', value: '218', width: '15%' },
                      { label: 'End-User Devices', value: '562', width: '40%' },
                    ].map((row, i) => (
                      <div key={i}>
                        <div className="flex justify-between items-center text-xs text-slate-700 dark:text-slate-300 mb-1">
                          <span>{row.label}</span>
                          <span className="font-bold">{row.value}</span>
                        </div>
                        <div className="w-full bg-slate-100 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden">
                          <div className="bg-primary h-full rounded-full" style={{ width: row.width }}></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="flex justify-center py-4">
                  <div className="w-40 h-40 rounded-full border-8 border-slate-50 dark:border-slate-800 relative flex items-center justify-center">
                    <div className="absolute inset-0 rounded-full border-8 border-primary border-t-transparent -rotate-45"></div>
                    <div className="text-center">
                      <p className="text-[10px] font-bold opacity-40 uppercase text-slate-500">PQC Ready</p>
                      <p className="text-3xl font-bold text-slate-900 dark:text-slate-100">72%</p>
                    </div>
                  </div>
                </div>
              </div>
              <div className="p-4 bg-slate-50 dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 flex justify-center">
                <p className="text-[10px] text-slate-400 font-bold tracking-widest uppercase">PAGE 1 OF 14 — CONFIDENTIAL</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportsPage;
