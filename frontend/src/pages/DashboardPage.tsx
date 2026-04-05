import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { assetsAPI, devAPI } from '../api/client';

interface Summary {
  total: number;
  critical: number;
  pqcReady: number;
  scanned: number;
}

const DashboardPage: React.FC = () => {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [assets, setAssets] = useState<any[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    // Fetch assets from backend via API client
    assetsAPI.listAssets(1, 100)
      .then((response: any) => {
        const items = response.items ?? [];
        setAssets(items);
        setSummary({
          total: items.length,
          // Assets with risk_score >= 7.0 considered critical
          critical: items.filter((a: any) => (a.risk_score ?? 0) >= 7.0).length,
          // Assets that have been scanned (status !== pending)
          scanned: items.filter((a: any) => a.status !== 'pending').length,
          // Assets with low risk score (<= 3.0)
          pqcReady: items.filter((a: any) => (a.risk_score ?? 0) <= 3.0).length,
        });
      })
      .catch((err) => console.error("Error fetching assets:", err));
  }, []);

  const RISK_COLOR: Record<string, string> = {
    critical: 'text-red-500', 
    high: 'text-orange-500',
    medium: 'text-amber-500', 
    low: 'text-green-500',
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      {/* Status Widgets */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {[
          { label: 'Total Assets', value: summary?.total ?? '...', icon: 'devices', color: 'text-primary' },
          { label: 'Scanned', value: summary?.total ?? '...', icon: 'biotech', color: 'text-primary' },
          { label: 'High Risk', value: summary?.critical ?? '...', icon: 'warning', color: 'text-red-500' },
          { label: 'PQC-Ready', value: summary?.pqcReady ?? '...', icon: 'verified_user', color: 'text-green-500' },
          { label: 'Non-Ready', value: (summary?.total ?? 0) - (summary?.pqcReady ?? 0) - (summary?.scanned ?? 0), icon: 'gpp_maybe', color: 'text-amber-500' },
          { label: 'Cert Expiring', value: '12', icon: 'timer', color: 'text-amber-500' },
        ].map((widget, i) => (
          <div key={i} className="bg-white dark:bg-slate-800/40 p-4 rounded-lg border border-slate-200 dark:border-slate-800 swing-border">
            <div className="flex justify-between items-start mb-2">
              <p className="text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">{widget.label}</p>
              <span className={`material-symbols-outlined ${widget.color} text-xl`}>{widget.icon}</span>
            </div>
            <p className={`text-2xl font-bold ${widget.label === 'High Risk' ? 'text-red-500' : ''}`}>{widget.value}</p>
            <p className={`text-[11px] ${widget.label === 'High Risk' || widget.label === 'Cert Expiring' ? 'text-red-500' : 'text-green-500'} mt-1 flex items-center font-medium`}>
              <span className="material-symbols-outlined text-[14px]">
                {widget.label === 'High Risk' || widget.label === 'Cert Expiring' ? 'arrow_downward' : 'arrow_upward'}
              </span> 5.2%
            </p>
          </div>
        ))}
      </div>

      {/* Security Alerts Section */}
      <div className="grid grid-cols-1 gap-4">
        <div className="bg-red-500/5 dark:bg-red-500/10 border border-red-500/20 rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-red-500">notifications_active</span>
              <h3 className="font-bold text-sm text-red-500 uppercase tracking-wider">Critical Security Alerts</h3>
            </div>
            <span className="px-2 py-0.5 bg-red-500 text-white text-[10px] font-black rounded italic">ACTION REQUIRED</span>
          </div>
          <div className="space-y-3">
            {[
              { title: 'Certificate Expiry Alert', target: 'api.prod.gateway.com', msg: 'Leaf certificate expiring in 12 days (RSA-2048)', severity: 'CRITICAL' },
              { title: 'Legacy Algorithm Detected', target: 'legacy.vault-01.internal', msg: '3DES detected in active handshake. Immediate migration required.', severity: 'HIGH' },
            ].map((alert, i) => (
              <div key={i} className="flex items-start justify-between bg-white dark:bg-slate-900/40 p-3 rounded border border-red-500/10 hover:border-red-500/30 transition-colors">
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded bg-red-500/20 flex items-center justify-center shrink-0">
                    <span className="material-symbols-outlined text-red-500 text-lg">{alert.severity === 'CRITICAL' ? 'priority_high' : 'warning'}</span>
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-900 dark:text-slate-100">{alert.title}</p>
                    <p className="text-[10px] text-slate-500 mt-0.5">Target: <span className="font-mono text-primary">{alert.target}</span></p>
                    <p className="text-[10px] text-red-500/80 mt-1">{alert.msg}</p>
                  </div>
                </div>
                <button className="px-3 py-1 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded text-[10px] font-bold transition-colors">FIX NOW</button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Grid: Activity & Risk */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Recent Scan Activity */}
        <div className="xl:col-span-2 bg-white dark:bg-slate-800/40 rounded-lg border border-slate-200 dark:border-slate-800 overflow-hidden flex flex-col">
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">history</span>
              <h3 className="font-bold text-sm">Recent Scan Activity (T vs T-1)</h3>
            </div>
            <button className="text-[11px] font-bold text-primary hover:underline">VIEW FULL HISTORY</button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead className="bg-slate-50 dark:bg-slate-900/50">
                <tr>
                  <th className="p-3 text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase">Host / Target</th>
                  <th className="p-3 text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase">Current Score</th>
                  <th className="p-3 text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase">Delta</th>
                  <th className="p-3 text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase">Result</th>
                  <th className="p-3 text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {[
                  { host: 'api.pqc-kyber.com', score: '1.2', delta: '-0.5', status: 'pqc_ready', trend: 'down' },
                  { host: 'legacy.vault-01.net', score: '9.4', delta: '+1.2', status: 'critical', trend: 'up' },
                  { host: 'portal.prod.bank.cn', score: '4.5', delta: '0.0', status: 'at_risk', trend: 'even' },
                ].map((asset, i) => (
                  <tr key={i} className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
                    <td className="p-3 text-xs font-mono">{asset.host}</td>
                    <td className={`p-3 text-xs font-bold ${asset.status === 'critical' ? 'text-red-500' : 'text-slate-700 dark:text-slate-300'}`}>{asset.score}</td>
                    <td className={`p-3 text-[10px] font-bold flex items-center gap-0.5 ${asset.trend === 'up' ? 'text-red-500' : asset.trend === 'down' ? 'text-green-500' : 'text-slate-400'}`}>
                      <span className="material-symbols-outlined text-[12px]">{asset.trend === 'up' ? 'trending_up' : asset.trend === 'down' ? 'trending_down' : 'trending_flat'}</span>
                      {asset.delta}
                    </td>
                    <td className="p-3">
                      <span className={`px-2 py-1 rounded-full text-[10px] font-bold uppercase ${
                        asset.status === 'pqc_ready' 
                          ? 'bg-teal-500/20 text-teal-400' 
                          : asset.status === 'critical' ? 'bg-red-500/20 text-red-500' : 'bg-amber-500/20 text-amber-500'
                      }`}>
                        {asset.status.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="p-3">
                      <button className="material-symbols-outlined text-slate-400 hover:text-primary transition-colors">compare_arrows</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Risk Level Summary */}
        <div className="bg-white dark:bg-slate-800/40 rounded-lg border border-slate-200 dark:border-slate-800 flex flex-col">
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center gap-2">
            <span className="material-symbols-outlined text-primary">donut_large</span>
            <h3 className="font-bold text-sm">Risk Level Summary</h3>
          </div>
          <div className="p-6 flex-1 flex flex-col justify-center">
            <div className="flex flex-col gap-6">
              {[
                { label: 'Critical Risk', value: '8%', color: 'bg-red-500', textColor: 'text-red-500' },
                { label: 'High Risk', value: '14%', color: 'bg-orange-500', textColor: 'text-orange-500' },
                { label: 'Medium Risk', value: '22%', color: 'bg-amber-500', textColor: 'text-amber-500' },
                { label: 'Safe / PQC Ready', value: '56%', color: 'bg-green-500', textColor: 'text-green-500' },
              ].map((risk, i) => (
                <div key={i}>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs font-medium">{risk.label}</span>
                    <span className={`text-xs font-bold ${risk.textColor}`}>{risk.value}</span>
                  </div>
                  <div className="w-full h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                    <div className={`h-full ${risk.color} rounded-full`} style={{ width: risk.value }}></div>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-8 pt-6 border-t border-slate-100 dark:border-slate-800 text-center">
              <p className="text-[11px] text-slate-500 dark:text-slate-400">SCAN COVERAGE</p>
              <p className="text-3xl font-bold text-primary">82.8%</p>
              <p className="text-[10px] text-slate-400 mt-1 italic">Scan completed 14 minutes ago</p>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Row: PQC Classification & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-slate-800/40 p-6 rounded-lg border border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-2 mb-6">
            <span className="material-symbols-outlined text-primary text-xl">pie_chart</span>
            <h3 className="font-bold text-sm tracking-tight uppercase">Inventory Distribution</h3>
          </div>
          <div className="grid grid-cols-2 gap-8">
            {/* Certs by Algorithm */}
            <div className="space-y-4">
               <p className="text-[10px] font-black text-slate-500 uppercase text-center">Certs by Algorithm</p>
               <div className="relative size-28 mx-auto">
                 <svg viewBox="0 0 36 36" className="size-full -rotate-90">
                    <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="#10b981" strokeWidth="3" strokeDasharray="60 40"></circle>
                    <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="#f59e0b" strokeWidth="3" strokeDasharray="25 75" strokeDashoffset="-60"></circle>
                    <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="#ef4444" strokeWidth="3" strokeDasharray="15 85" strokeDashoffset="-85"></circle>
                 </svg>
                 <div className="absolute inset-0 flex items-center justify-center text-[10px] font-black">RSA/ECC</div>
               </div>
               <div className="flex flex-col gap-1">
                 <div className="flex items-center justify-between text-[9px] font-bold"><span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500"></span> RSA-4096</span> <span>60%</span></div>
                 <div className="flex items-center justify-between text-[9px] font-bold"><span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500"></span> ECDSA-256</span> <span>25%</span></div>
                 <div className="flex items-center justify-between text-[9px] font-bold"><span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500"></span> RSA-2048</span> <span>15%</span></div>
               </div>
            </div>
            {/* Protocols */}
            <div className="space-y-4">
               <p className="text-[10px] font-black text-slate-500 uppercase text-center">Protocol Drift</p>
               <div className="relative size-28 mx-auto">
                 <svg viewBox="0 0 36 36" className="size-full -rotate-90">
                    <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="#0ea5e9" strokeWidth="4" strokeDasharray="80 20"></circle>
                    <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="#f43f5e" strokeWidth="4" strokeDasharray="20 80" strokeDashoffset="-80"></circle>
                 </svg>
                 <div className="absolute inset-0 flex items-center justify-center text-[10px] font-black">TLS 1.3</div>
               </div>
               <div className="flex flex-col gap-1">
                 <div className="flex items-center justify-between text-[9px] font-bold"><span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-primary font-black animate-pulse"></span> TLS 1.3</span> <span>80.2%</span></div>
                 <div className="flex items-center justify-between text-[9px] font-bold"><span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500"></span> Legacy (1.2/1.1)</span> <span>19.8%</span></div>
               </div>
            </div>
          </div>
        </div>
        <div className="bg-primary text-white p-6 rounded-lg border border-primary relative overflow-hidden group">
          <div className="relative z-10 h-full flex flex-col justify-between">
            <div>
              <h3 className="text-xl font-bold mb-2">Initialize Global Scan</h3>
              <p className="text-white/80 text-xs opacity-90 leading-relaxed max-w-sm">
                Run a comprehensive quantum-risk assessment across all registered endpoints and cloud assets in your organization.
              </p>
            </div>
            <div className="flex gap-4">
              <button 
                onClick={() => navigate('/scan')}
                className="px-4 py-2 bg-white text-primary rounded font-bold text-xs hover:bg-slate-100 transition-colors"
              >
                START NEW SCAN
              </button>
              <button 
                onClick={async () => {
                  try {
                    await devAPI.simulateScan();
                    alert('Simulation Triggered! Scans are running in the background.');
                  } catch (e) {
                    console.error('Simulation failed', e);
                    alert('Failed to trigger simulation. Check console for details.');
                  }
                }}
                className="px-4 py-2 bg-primary/20 border border-white/30 rounded font-bold text-xs hover:bg-white/10 transition-colors"
              >
                SIMULATE SCHEDULED SCAN
              </button>
            </div>
          </div>
          <span className="material-symbols-outlined absolute -bottom-10 -right-10 text-[180px] opacity-10 pointer-events-none group-hover:scale-110 transition-transform">bolt</span>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
