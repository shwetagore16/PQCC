import React, { useEffect, useState } from 'react';
import { assetsAPI } from '../api/client';

interface ClassificationData {
  grade: string;
  count: number;
  color: string;
}

interface ApplicationStatusData {
  label: string;
  value: number;
  color: string;
}

interface RiskAsset {
  id?: string;
  name: string;
  domain: string;
  pqcSupport: 'Ready' | 'Not Ready';
}

interface PqcCbomUpdate {
  assetId: string;
  name: string;
  domain: string;
  pqcStatus: string;
  riskScore: number;
  updatedAt: string;
}

const PQCClassificationPage: React.FC = () => {
  const classificationData: ClassificationData[] = [
    { grade: 'Elite', count: 37, color: '#10b981' },
    { grade: 'Critical', count: 2, color: '#ef4444' },
    { grade: 'Std', count: 4, color: '#8b5cf6' },
  ];

  const applicationStatusData: ApplicationStatusData[] = [
    { label: 'Elite-PQC Ready', value: 45, color: '#10b981' },
    { label: 'Standard', value: 30, color: '#f59e0b' },
    { label: 'Legacy', value: 15, color: '#f97316' },
    { label: 'Critical', value: 10, color: '#ef4444' },
  ];

  const initialRiskAssets: RiskAsset[] = [
    { name: 'digigrihavatika.pnbatt.bank.in', domain: '(103.109.225.128)', pqcSupport: 'Ready' },
    { name: 'wcw.pnb.bank.in', domain: '(103.109.225.201)', pqcSupport: 'Ready' },
    { name: 'Wbbgb.pnbubk.bank.in', domain: '(103.109.224.249)', pqcSupport: 'Not Ready' },
  ];

  const [riskAssets, setRiskAssets] = useState<RiskAsset[]>(initialRiskAssets);
  const POLL_INTERVAL_MS = 20000;

  useEffect(() => {
    let isMounted = true;

    const applyUpdate = (payload: PqcCbomUpdate) => {
      const pqcSupport: RiskAsset['pqcSupport'] = payload.pqcStatus === 'PQC_READY' ? 'Ready' : 'Not Ready';
      const domainLabel = payload.domain ? payload.domain : '(Uploaded CBOM)';
      const nextAsset: RiskAsset = {
        id: payload.assetId,
        name: payload.name || `Asset ${payload.assetId}`,
        domain: domainLabel,
        pqcSupport,
      };

      setRiskAssets((prev) => {
        const existingIndex = prev.findIndex((asset) => asset.id === payload.assetId || asset.name === nextAsset.name);
        if (existingIndex >= 0) {
          const updated = [...prev];
          updated[existingIndex] = { ...updated[existingIndex], ...nextAsset };
          return updated;
        }
        return [nextAsset, ...prev];
      });
    };

    const loadStoredUpdates = () => {
      try {
        const stored = localStorage.getItem('pqcCbomUpdates');
        if (!stored) return;
        const parsed = JSON.parse(stored) as Record<string, PqcCbomUpdate>;
        Object.values(parsed).forEach((payload) => applyUpdate(payload));
      } catch (error) {
        console.warn('Failed to load PQC updates', error);
      }
    };

    const applyAssetSnapshot = (items: any[]) => {
      if (!items.length) return;
      const mapped: RiskAsset[] = items.map((asset) => {
        const pqcSupport: RiskAsset['pqcSupport'] = (asset.risk_score ?? 0) <= 3 ? 'Ready' : 'Not Ready';
        return {
          id: asset.id,
          name: asset.asset_value || `Asset ${asset.id}`,
          domain: asset.seed_domain ? `(${asset.seed_domain})` : '(Uploaded CBOM)',
          pqcSupport,
        };
      });

      setRiskAssets((prev) => {
        const prevById = new Map(prev.filter((asset) => asset.id).map((asset) => [asset.id, asset]));
        const merged = mapped.map((asset) => {
          const existing = asset.id ? prevById.get(asset.id) : undefined;
          return existing ? { ...asset, ...existing } : asset;
        });
        const extras = prev.filter((asset) => asset.id && !mapped.some((item) => item.id === asset.id));
        return [...merged, ...extras];
      });
    };

    const fetchAssets = async () => {
      try {
        const response: any = await assetsAPI.listAssets(1, 200);
        if (!isMounted) return;
        const items = response.items ?? [];
        applyAssetSnapshot(items);
        loadStoredUpdates();
      } catch (error) {
        if (isMounted) {
          console.warn('Failed to refresh assets for PQC dashboard', error);
        }
      }
    };

    const handleCustomUpdate = (event: Event) => {
      const detail = (event as CustomEvent<PqcCbomUpdate>).detail;
      if (detail) {
        applyUpdate(detail);
      }
    };

    const handleStorageUpdate = (event: StorageEvent) => {
      if (event.key === 'pqcCbomUpdates') {
        loadStoredUpdates();
      }
    };

    loadStoredUpdates();
    fetchAssets();
    const intervalId = window.setInterval(fetchAssets, POLL_INTERVAL_MS);
    window.addEventListener('pqc-cbom-updated', handleCustomUpdate as EventListener);
    window.addEventListener('storage', handleStorageUpdate);

    return () => {
      isMounted = false;
      window.clearInterval(intervalId);
      window.removeEventListener('pqc-cbom-updated', handleCustomUpdate as EventListener);
      window.removeEventListener('storage', handleStorageUpdate);
    };
  }, []);

  const getMaxCount = () => Math.max(...classificationData.map(d => d.count));
  const maxCount = getMaxCount();

  // Calculate pie chart segments
  const pieData = applicationStatusData.map((item, idx) => {
    const percentage = item.value;
    return {
      ...item,
      startAngle: applicationStatusData.slice(0, idx).reduce((sum, d) => sum + (d.value * 3.6), 0),
      angle: percentage * 3.6,
    };
  });

  const getPiePath = (startAngle: number, angle: number) => {
    const start = ((startAngle - 90) * Math.PI) / 180;
    const end = (((startAngle + angle) - 90) * Math.PI) / 180;
    const x1 = 100 + 80 * Math.cos(start);
    const y1 = 100 + 80 * Math.sin(start);
    const x2 = 100 + 80 * Math.cos(end);
    const y2 = 100 + 80 * Math.sin(end);
    const largeArc = angle > 180 ? 1 : 0;
    return `M 100 100 L ${x1} ${y1} A 80 80 0 ${largeArc} 1 ${x2} ${y2} Z`;
  };

  return (
    <div className="flex-1 overflow-y-auto bg-background-light dark:bg-background-dark p-6 font-display">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">PQC Compliance Dashboard</h1>
            <div className="flex gap-6 mt-2 text-xs font-bold">
              <span className="text-emerald-600">Elite-PQC Ready: 45%</span>
              <span className="text-amber-600">Standard: 30%</span>
              <span className="text-orange-600">Legacy: 15%</span>
              <span className="text-red-600">Critical Apps: 8</span>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="px-4 py-2 rounded text-sm font-medium text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors flex items-center gap-2">
              <span className="material-symbols-outlined text-sm">refresh</span> Re-scan
            </button>
            <button className="bg-primary hover:bg-primary/90 px-4 py-2 rounded text-sm font-medium text-white flex items-center gap-2 shadow-lg shadow-primary/20 transition-all active:scale-95">
              <span className="material-symbols-outlined text-sm">download</span> Export Data
            </button>
          </div>
        </div>

        {/* Visualizations Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Classification Grade Chart */}
          <div className="bg-white dark:bg-panel-dark rounded-lg border border-slate-200 dark:border-border-dark p-6 shadow-sm">
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 mb-6">Assets by Classification Grade</h3>
            <div className="flex items-end justify-around h-48 gap-4">
              {classificationData.map((item) => (
                <div key={item.grade} className="flex flex-col items-center flex-1">
                  <div className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">{item.count}</div>
                  <div
                    className="w-full rounded-t transition-all hover:opacity-80"
                    style={{
                      height: `${(item.count / maxCount) * 150}px`,
                      backgroundColor: item.color,
                    }}
                  ></div>
                  <div className="text-xs font-bold text-slate-600 dark:text-slate-400 mt-2 text-center">{item.grade}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Application Status Pie Chart */}
          <div className="bg-white dark:bg-panel-dark rounded-lg border border-slate-200 dark:border-border-dark p-6 shadow-sm">
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 mb-6">Application Status</h3>
            <div className="flex items-center justify-center">
              <svg viewBox="0 0 200 200" className="w-32 h-32">
                {pieData.map((item, idx) => (
                  <path
                    key={idx}
                    d={getPiePath(item.startAngle, item.angle)}
                    fill={item.color}
                    opacity="0.85"
                    stroke="white"
                    strokeWidth="2"
                    className="dark:stroke-panel-dark"
                  />
                ))}
              </svg>
            </div>
            <div className="mt-6 space-y-2">
              {applicationStatusData.map((item) => (
                <div key={item.label} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }}></div>
                    <span className="text-slate-600 dark:text-slate-400">{item.label}</span>
                  </div>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{item.value}%</span>
                </div>
              ))}
            </div>
          </div>

          {/* Risk Overview Heatmap */}
          <div className="bg-white dark:bg-panel-dark rounded-lg border border-slate-200 dark:border-border-dark p-6 shadow-sm">
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 mb-6">Risk Overview</h3>
            <div className="grid grid-cols-3 gap-2 mb-6">
              {[
                ['#ef4444', '#ef4444', '#f97316'],
                ['#f59e0b', '#fbbf24', '#10b981'],
                ['#fbbf24', '#10b981', '#10b981'],
              ].map((row, rIdx) => (
                <div key={rIdx} className="contents">
                  {row.map((color, cIdx) => (
                    <div
                      key={`${rIdx}-${cIdx}`}
                      className="aspect-square rounded border border-slate-200 dark:border-border-dark hover:scale-110 transition-transform cursor-pointer"
                      style={{ backgroundColor: color, opacity: 0.8 }}
                      title="Risk cell"
                    ></div>
                  ))}
                </div>
              ))}
            </div>
            <div className="grid grid-cols-3 text-center gap-2 text-xs font-bold">
              <div className="flex items-center justify-center gap-1">
                <div className="w-2 h-2 rounded" style={{ backgroundColor: '#ef4444' }}></div>
                <span className="text-slate-600 dark:text-slate-400">High Risk</span>
              </div>
              <div className="flex items-center justify-center gap-1">
                <div className="w-2 h-2 rounded" style={{ backgroundColor: '#fbbf24' }}></div>
                <span className="text-slate-600 dark:text-slate-400">Medium Risk</span>
              </div>
              <div className="flex items-center justify-center gap-1">
                <div className="w-2 h-2 rounded" style={{ backgroundColor: '#10b981' }}></div>
                <span className="text-slate-600 dark:text-slate-400">Safe</span>
              </div>
            </div>
          </div>
        </div>

        {/* Assets Table and Details Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Assets Table */}
          <div className="lg:col-span-2 bg-white dark:bg-panel-dark rounded-lg border border-slate-200 dark:border-border-dark shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-200 dark:border-border-dark bg-slate-50 dark:bg-black/20">
              <h3 className="font-bold text-slate-800 dark:text-slate-200">Assets Name</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 dark:bg-black/20 border-b border-slate-200 dark:border-border-dark">
                    <th className="px-6 py-3 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Asset Name</th>
                    <th className="px-6 py-3 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">PQC Support</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-border-dark">
                  {riskAssets.map((asset, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-white/5 transition-colors">
                      <td className="px-6 py-4 text-sm">
                        <div className="font-bold text-slate-900 dark:text-slate-100">{asset.name}</div>
                        <div className="text-xs text-slate-500 dark:text-slate-400">{asset.domain}</div>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold ${
                            asset.pqcSupport === 'Ready'
                              ? 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30'
                              : 'bg-red-500/20 text-red-600 dark:text-red-400 border border-red-500/30'
                          }`}
                        >
                          <span className="material-symbols-outlined text-sm">
                            {asset.pqcSupport === 'Ready' ? 'check' : 'close'}
                          </span>
                          {asset.pqcSupport}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* App Details Card */}
          <div className="bg-white dark:bg-panel-dark rounded-lg border border-slate-200 dark:border-border-dark p-6 shadow-sm">
            <h3 className="font-bold text-slate-800 dark:text-slate-200 mb-6 flex items-center gap-2">
              <span className="material-symbols-outlined">info</span>
              App A Details
            </h3>
            <div className="space-y-4">
              <div className="flex items-center gap-3 pb-4 border-b border-slate-200 dark:border-border-dark">
                <span className="material-symbols-outlined text-slate-500">apps</span>
                <div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">Application</div>
                  <div className="font-bold text-slate-900 dark:text-slate-100">App A</div>
                </div>
              </div>
              <div className="flex items-center gap-3 pb-4 border-b border-slate-200 dark:border-border-dark">
                <span className="material-symbols-outlined text-slate-500">person</span>
                <div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">Owner</div>
                  <div className="font-bold text-slate-900 dark:text-slate-100">Team 1</div>
                </div>
              </div>
              <div className="flex items-center gap-3 pb-4 border-b border-slate-200 dark:border-border-dark">
                <span className="material-symbols-outlined text-slate-500">language</span>
                <div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">Exposure</div>
                  <div className="font-bold text-slate-900 dark:text-slate-100">Internet</div>
                </div>
              </div>
              <div className="flex items-center gap-3 pb-4 border-b border-slate-200 dark:border-border-dark">
                <span className="material-symbols-outlined text-slate-500">security</span>
                <div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">TLS</div>
                  <div className="font-bold text-slate-900 dark:text-slate-100">RSA / ECC</div>
                </div>
              </div>
              <div className="flex items-center gap-3 pb-4 border-b border-slate-200 dark:border-border-dark">
                <span className="material-symbols-outlined text-red-500">warning</span>
                <div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">Score</div>
                  <div className="font-bold text-red-600 dark:text-red-400">480 (Critical)</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-slate-500">check_circle</span>
                <div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">Status</div>
                  <div className="font-bold text-slate-900 dark:text-slate-100">Legacy</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Improvement Recommendations */}
        <div className="bg-white dark:bg-panel-dark rounded-lg border border-slate-200 dark:border-border-dark p-6 shadow-sm">
          <h3 className="font-bold text-slate-800 dark:text-slate-200 mb-4">Improvement Recommendations</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { icon: 'upgrade', text: 'Upgrade to TLS 1.3 with PQC' },
              { icon: 'vpn_key', text: 'Implement Kyber for Key Exchange' },
              { icon: 'library_books', text: 'Update Cryptographic Libraries' },
              { icon: 'timeline', text: 'Develop PQC Migration Plan' },
            ].map((rec, idx) => (
              <div key={idx} className="p-4 rounded border border-slate-200 dark:border-border-dark hover:bg-slate-50 dark:hover:bg-white/5 transition-colors flex items-center gap-3 cursor-pointer">
                <span className="material-symbols-outlined text-slate-500 dark:text-slate-400">{rec.icon}</span>
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{rec.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PQCClassificationPage;
