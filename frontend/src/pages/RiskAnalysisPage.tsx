import React from 'react';

const RiskAnalysisPage: React.FC = () => {
  return (
    <div className="flex-1 overflow-y-auto bg-slate-50 dark:bg-background-dark/50 p-8 font-display">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Risk Header & Categories */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h2 className="text-3xl font-bold text-slate-900 dark:text-slate-100">Asset Risk Profile</h2>
            <p className="text-slate-500 text-sm mt-1">Snapshot of vulnerabilities and configuration posture for <span className="text-primary underline">prod-db-cluster-01</span></p>
          </div>
          <div className="flex gap-2 text-slate-900 dark:text-slate-100">
            <div className="flex items-center gap-2 px-3 py-1 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-500 text-xs font-bold uppercase tracking-wider">Low</div>
            <div className="flex items-center gap-2 px-3 py-1 rounded bg-yellow-500/10 border border-yellow-500/30 text-yellow-500 text-xs font-bold uppercase tracking-wider">Med</div>
            <div className="flex items-center gap-2 px-3 py-1 rounded bg-orange-500/10 border border-orange-500/30 text-orange-500 text-xs font-bold uppercase tracking-wider">High</div>
            <div className="flex items-center gap-2 px-3 py-1 rounded bg-red-500 text-white text-xs font-bold uppercase tracking-wider shadow-lg shadow-red-500/20 ring-2 ring-red-500 ring-offset-2 ring-offset-background-dark">Crit</div>
          </div>
        </div>

        {/* Main Risk Card Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Score Card */}
          <div className="lg:col-span-1 bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 rounded-xl p-8 flex flex-col items-center justify-center relative overflow-hidden shadow-sm">
            <div className="absolute inset-0 bg-gradient-to-br from-red-500/5 to-transparent pointer-events-none"></div>
            <h3 className="text-sm font-bold uppercase text-slate-500 mb-8 tracking-widest">Aggregate Score</h3>
            {/* Circular Meter */}
            <div className="relative w-48 h-48">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                <circle className="text-slate-200 dark:text-slate-700" cx="50" cy="50" fill="transparent" r="40" stroke="currentColor" strokeWidth="10"></circle>
                <circle className="text-red-500" cx="50" cy="50" fill="transparent" r="40" stroke="currentColor" strokeWidth="10" strokeDasharray="251.2" strokeDashoffset="37.68" strokeLinecap="round"></circle>
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-5xl font-black text-red-500">85</span>
                <span className="text-xs font-bold text-slate-500">/ 100</span>
              </div>
            </div>
            <div className="mt-8 text-center">
              <p className="text-red-500 font-bold mb-1">Critical Exposure</p>
              <p className="text-slate-500 text-xs px-4">Based on current network configuration and internal threat intelligence.</p>
            </div>
          </div>

          {/* Contributing Factors */}
          <div className="lg:col-span-2 bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 rounded-xl flex flex-col overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex justify-between items-center bg-slate-50 dark:bg-slate-800/30">
              <h3 className="text-sm font-bold flex items-center gap-2 text-slate-900 dark:text-slate-100">
                <span className="material-symbols-outlined text-orange-500">list_alt</span>
                Contributing Risk Factors
              </h3>
              <span className="text-[10px] text-slate-500 uppercase font-bold tracking-tighter">Impact Weighting</span>
            </div>
            <div className="p-6 space-y-4">
              {[
                { label: 'Legacy Cipher Suites Enabled', icon: 'lock_open', color: 'red', pts: '+42 pts', width: '85%' },
                { label: 'Weak TLS Configuration (TLS 1.0/1.1)', icon: 'key_off', color: 'orange', pts: '+28 pts', width: '60%' },
                { label: 'Unpatched CVE-2023-44487', icon: 'history', color: 'yellow', pts: '+15 pts', width: '35%' },
              ].map((factor, i) => (
                <div key={i} className="flex items-center gap-4 group">
                  <div className={`size-10 rounded bg-${factor.color}-500/10 border border-${factor.color}-500/20 flex items-center justify-center flex-shrink-0`}>
                    <span className={`material-symbols-outlined text-${factor.color}-500 text-lg`}>{factor.icon}</span>
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between items-start mb-1">
                      <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">{factor.label}</h4>
                      <span className={`text-xs text-${factor.color}-400 font-mono`}>{factor.pts}</span>
                    </div>
                    <div className="w-full bg-slate-200 dark:bg-slate-700 h-1.5 rounded-full">
                      <div className={`bg-${factor.color}-500 h-full rounded-full`} style={{ width: factor.width }}></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Attack Path Visualization */}
        <div className="bg-white dark:bg-slate-900 shadow-xl rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-800/50">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-red-500">hub</span>
              <h3 className="font-black text-xs uppercase tracking-widest text-slate-700 dark:text-slate-300">Quantum-Vector Attack Path</h3>
            </div>
            <span className="text-[10px] text-red-500 font-bold bg-red-500/10 px-2 py-0.5 rounded border border-red-500/20">3 HOPS TO DATA EXFILTRATION</span>
          </div>
          <div className="p-10 flex flex-col md:flex-row items-center justify-center gap-8 md:gap-4 lg:gap-12 relative">
            {/* The actual "Graph" */}
            {[
              { id: 'EXT', label: 'External Entry', name: 'api.prod.gateway', icon: 'public', risk: 'critical' },
              { id: 'MID', label: 'Auth Middleware', name: 'auth-v1.proxy', icon: 'shield', risk: 'high' },
              { id: 'TGT', label: 'Target Vault', name: 'prod-secrets-01', icon: 'database', risk: 'critical' },
            ].map((node, i, arr) => (
              <React.Fragment key={node.id}>
                <div className="flex flex-col items-center group relative cursor-help">
                  <div className={`size-16 rounded-full flex items-center justify-center border-4 transition-all group-hover:scale-110 shadow-lg ${
                    node.risk === 'critical' ? 'bg-red-500/10 border-red-500 text-red-500 shadow-red-500/20' : 'bg-orange-500/10 border-orange-500 text-orange-500 shadow-orange-500/20'
                  }`}>
                    <span className="material-symbols-outlined text-3xl">{node.icon}</span>
                  </div>
                  <div className="mt-4 text-center">
                    <p className="text-[10px] font-black text-slate-500 uppercase tracking-tighter">{node.label}</p>
                    <p className="text-xs font-mono font-bold text-slate-900 dark:text-slate-100">{node.name}</p>
                  </div>
                  {/* Tooltip Simulation */}
                  <div className="absolute -top-12 left-1/2 -translate-x-1/2 bg-slate-800 text-white text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-20">
                    CVSS: 9.8 | PQC: {node.risk === 'critical' ? 'NOT READY' : 'READY'}
                  </div>
                </div>
                {i < arr.length - 1 && (
                  <div className="hidden md:flex flex-col items-center flex-1 min-w-[40px] gap-1">
                    <div className="h-px bg-gradient-to-r from-red-500 to-orange-500 w-full relative">
                      <span className="material-symbols-outlined absolute -right-2 -top-2 text-orange-500 text-sm">chevron_right</span>
                    </div>
                    <span className="text-[9px] font-bold text-slate-400">Broken PKE</span>
                  </div>
                )}
                {i < arr.length - 1 && (
                  <div className="md:hidden h-8 w-px bg-slate-300 dark:bg-slate-700"></div>
                )}
              </React.Fragment>
            ))}
          </div>
          <div className="px-6 py-3 bg-red-500/5 text-center text-[10px] text-red-400 font-bold border-t border-slate-100 dark:border-slate-800">
            DETECTED VIA GRAPH NEURAL NETWORK (GNN) TOPOLOGY ANALYSIS
          </div>
        </div>

        {/* Key Risk Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* HNDL Score Card */}
          <div className="bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 rounded-xl p-6 shadow-sm">
            <div className="flex items-start justify-between mb-6">
              <div>
                <h3 className="text-sm font-bold uppercase text-slate-500 tracking-widest mb-2">HNDL Score</h3>
                <p className="text-xs text-slate-400">Hardware-Network-Database-Logic Assessment</p>
              </div>
              <span className="material-symbols-outlined text-slate-400">info</span>
            </div>
            <div className="flex items-end gap-4">
              <div className="flex-1">
                <div className="text-4xl font-black text-orange-500 mb-2">72</div>
                <div className="text-xs text-slate-500 mb-3">Out of 100</div>
                <div className="w-full bg-slate-200 dark:bg-slate-700 h-2 rounded-full overflow-hidden">
                  <div className="bg-gradient-to-r from-orange-400 to-orange-500 h-full" style={{ width: '72%' }}></div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs font-bold text-orange-500 mb-1">⚠ MEDIUM</div>
                <div className="text-[10px] text-slate-500">Needs attention</div>
              </div>
            </div>
            <div className="mt-4 p-3 bg-orange-500/5 rounded border border-orange-500/20">
              <p className="text-xs text-slate-600 dark:text-slate-400">Hardware: 68 | Network: 75 | Database: 71 | Logic: 74</p>
            </div>
          </div>

          {/* Crypto Agility Score Card */}
          <div className="bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 rounded-xl p-6 shadow-sm">
            <div className="flex items-start justify-between mb-6">
              <div>
                <h3 className="text-sm font-bold uppercase text-slate-500 tracking-widest mb-2">Crypto Agility Score</h3>
                <p className="text-xs text-slate-400">Algorithm Migration Readiness</p>
              </div>
              <span className="material-symbols-outlined text-slate-400">info</span>
            </div>
            <div className="flex items-end gap-4">
              <div className="flex-1">
                <div className="text-4xl font-black text-amber-500 mb-2">58</div>
                <div className="text-xs text-slate-500 mb-3">Out of 100</div>
                <div className="w-full bg-slate-200 dark:bg-slate-700 h-2 rounded-full overflow-hidden">
                  <div className="bg-gradient-to-r from-amber-400 to-amber-500 h-full" style={{ width: '58%' }}></div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs font-bold text-amber-500 mb-1">⚠ LOW</div>
                <div className="text-[10px] text-slate-500">Limited flexibility</div>
              </div>
            </div>
            <div className="mt-4 p-3 bg-amber-500/5 rounded border border-amber-500/20">
              <p className="text-xs text-slate-600 dark:text-slate-400">Hybrid support: 45% | API modularity: 62% | Fallback mechanisms: 68%</p>
            </div>
          </div>
        </div>

        {/* Migration Forecast Section */}
        <div className="bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-950/20 dark:to-cyan-950/20 border border-blue-200 dark:border-blue-800/30 rounded-xl p-8 shadow-sm">
          <div className="flex items-start gap-4 mb-6">
            <span className="material-symbols-outlined text-blue-600 dark:text-blue-400 text-3xl">timeline</span>
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">Migration Forecast & Expected Outcomes</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">Projected risk reduction and security posture improvements following recommended remediation</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
            {/* Current State */}
            <div className="bg-white dark:bg-slate-900/60 rounded-lg p-6 border border-slate-200 dark:border-slate-700">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">Current State</h4>
                <span className="text-xs font-bold bg-red-500/10 text-red-600 dark:text-red-400 px-2 py-1 rounded">NOW</span>
              </div>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">Risk Score</span>
                    <span className="text-lg font-bold text-red-500">85/100</span>
                  </div>
                  <div className="w-full bg-slate-200 dark:bg-slate-700 h-2 rounded-full overflow-hidden">
                    <div className="bg-red-500 h-full" style={{ width: '85%' }}></div>
                  </div>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded space-y-2">
                  <div className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300">
                    <span className="material-symbols-outlined text-sm text-red-500">close</span>
                    <span>TLS 1.0/1.1 Active</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300">
                    <span className="material-symbols-outlined text-sm text-red-500">close</span>
                    <span>RSA-2048 Only</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300">
                    <span className="material-symbols-outlined text-sm text-red-500">close</span>
                    <span>No PQC Support</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Transition Arrow */}
            <div className="hidden lg:flex flex-col items-center justify-center gap-2">
              <div className="flex-1 border-l-2 border-dashed border-blue-400"></div>
              <span className="material-symbols-outlined text-blue-500 text-3xl">arrow_downward</span>
              <div className="flex-1 border-l-2 border-dashed border-blue-400"></div>
            </div>

            {/* Projected State (After Migration) */}
            <div className="bg-white dark:bg-slate-900/60 rounded-lg p-6 border border-emerald-200 dark:border-emerald-700/30">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">Post-Migration</h4>
                <span className="text-xs font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-2 py-1 rounded">12-16 WEEKS</span>
              </div>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">Risk Score</span>
                    <span className="text-lg font-bold text-emerald-500">31/100</span>
                  </div>
                  <div className="w-full bg-slate-200 dark:bg-slate-700 h-2 rounded-full overflow-hidden">
                    <div className="bg-emerald-500 h-full" style={{ width: '31%' }}></div>
                  </div>
                  <div className="text-xs text-emerald-600 dark:text-emerald-400 font-bold mt-2">↓ 54 points reduction</div>
                </div>
                <div className="p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded space-y-2">
                  <div className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300">
                    <span className="material-symbols-outlined text-sm text-emerald-500">check</span>
                    <span>TLS 1.3 Enforced</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300">
                    <span className="material-symbols-outlined text-sm text-emerald-500">check</span>
                    <span>Hybrid RSA + Kyber</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300">
                    <span className="material-symbols-outlined text-sm text-emerald-500">check</span>
                    <span>PQC Ready</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Migration Timeline & Impact */}
          <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-blue-500/10 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800/30 rounded-lg p-4">
              <h5 className="text-xs font-bold text-blue-600 dark:text-blue-400 uppercase mb-2">Timeline</h5>
              <div className="text-sm font-bold text-slate-900 dark:text-slate-100">12-16 weeks</div>
              <div className="text-xs text-slate-600 dark:text-slate-400 mt-1">Phased rollout with testing</div>
            </div>
            <div className="bg-emerald-500/10 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800/30 rounded-lg p-4">
              <h5 className="text-xs font-bold text-emerald-600 dark:text-emerald-400 uppercase mb-2">Risk Reduction</h5>
              <div className="text-sm font-bold text-slate-900 dark:text-slate-100">63.5%</div>
              <div className="text-xs text-slate-600 dark:text-slate-400 mt-1">From 85 → 31 score</div>
            </div>
            <div className="bg-amber-500/10 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800/30 rounded-lg p-4">
              <h5 className="text-xs font-bold text-amber-600 dark:text-amber-400 uppercase mb-2">Downtime</h5>
              <div className="text-sm font-bold text-slate-900 dark:text-slate-100">&lt; 2 hours</div>
              <div className="text-xs text-slate-600 dark:text-slate-400 mt-1">During final cutover</div>
            </div>
            <div className="bg-cyan-500/10 dark:bg-cyan-900/20 border border-cyan-200 dark:border-cyan-800/30 rounded-lg p-4">
              <h5 className="text-xs font-bold text-cyan-600 dark:text-cyan-400 uppercase mb-2">Status</h5>
              <div className="text-sm font-bold text-slate-900 dark:text-slate-100">Ready</div>
              <div className="text-xs text-slate-600 dark:text-slate-400 mt-1">Can start immediately</div>
            </div>
          </div>
        </div>

        {/* Recommendation Box */}
        <div className="bg-primary/5 border border-primary/30 rounded-xl p-6 flex items-start gap-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <span className="material-symbols-outlined text-6xl text-primary">psychology</span>
          </div>
          <div className="size-12 rounded-full bg-primary flex items-center justify-center flex-shrink-0 shadow-lg shadow-primary/30">
            <span className="material-symbols-outlined text-white text-2xl">bolt</span>
          </div>
          <div className="flex-1 space-y-4">
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">Priority Remediation Plan</h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 max-w-2xl">The engine suggests the following immediate actions to reduce the risk score by <span className="text-emerald-500 font-bold">54 points</span>.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white dark:bg-slate-900/60 p-4 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-primary/50 cursor-pointer shadow-sm">
                <div className="flex items-center gap-3 mb-2">
                  <span className="material-symbols-outlined text-primary text-sm">check_circle</span>
                  <h4 className="text-sm font-bold uppercase tracking-tight text-slate-900 dark:text-slate-100">Disable SSLv3/TLS 1.0</h4>
                </div>
                <p className="text-xs text-slate-500 leading-relaxed">Modify the proxy configuration to enforce TLS 1.2 or higher. Estimated downtime: 0ms.</p>
              </div>
              <div className="bg-white dark:bg-slate-900/60 p-4 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-primary/50 cursor-pointer shadow-sm">
                <div className="flex items-center gap-3 mb-2">
                  <span className="material-symbols-outlined text-primary text-sm">check_circle</span>
                  <h4 className="text-sm font-bold uppercase tracking-tight text-slate-900 dark:text-slate-100">Rotate Production Keys</h4>
                </div>
                <p className="text-xs text-slate-500 leading-relaxed">Detected key age exceeds policy (365 days). Recommended rotation via Vault.</p>
              </div>
            </div>
            <div className="pt-2">
              <button className="bg-primary hover:bg-primary/80 text-white font-bold py-2 px-6 rounded text-sm transition-colors flex items-center gap-2 shadow-lg shadow-primary/20 scale-100 active:scale-95 transition-all">
                <span className="material-symbols-outlined text-sm">rocket_launch</span>
                Execute Automatic Remediation
              </button>
            </div>
          </div>
        </div>

        {/* Secondary Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pb-8">
          {[
            { label: 'Internal Users', value: '1,248', sub: '2.4% vs last scan', icon: 'trending_up', trend: 'up' },
            { label: 'Endpoint Agents', value: '98.2%', sub: 'Status: Operational', icon: '', trend: '' },
            { label: 'Threat Intelligence', value: '4 Live', sub: 'Active exploits detected', icon: 'warning', trend: 'warn' },
            { label: 'Last Scan', value: '12m 45s ago', sub: 'Scan ID: #AS-992-B', icon: '', trend: 'italic' },
          ].map((stat, i) => (
            <div key={i} className="bg-white dark:bg-slate-900/30 p-4 rounded-lg border border-slate-200 dark:border-slate-800 flex flex-col shadow-sm">
              <span className="text-xs text-slate-500 font-bold uppercase mb-2 tracking-wider">{stat.label}</span>
              <span className="text-2xl font-bold text-slate-900 dark:text-slate-100">{stat.value}</span>
              <span className={`text-[10px] mt-1 flex items-center gap-1 ${stat.trend === 'up' ? 'text-emerald-500' : stat.trend === 'warn' ? 'text-red-500 font-bold' : stat.trend === 'italic' ? 'text-slate-500 italic' : 'text-slate-500'}`}>
                {stat.icon && <span className="material-symbols-outlined text-[10px]">{stat.icon}</span>}
                {stat.sub}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RiskAnalysisPage;
