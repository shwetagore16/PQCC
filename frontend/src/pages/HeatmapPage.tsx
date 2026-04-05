import React from 'react';
import { Map } from 'lucide-react';

const HeatmapPage: React.FC = () => {
  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-4">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">PQC Risk Heatmap</h1>
      <p className="text-sm text-slate-500 dark:text-gray-400">D3.js squarify treemap — cell size = HNDL score, color = risk band</p>
      <div className="bg-white/5 backdrop-blur-sm border border-slate-200 dark:border-white/10 rounded-2xl p-8 text-center text-gray-500">
        <Map className="h-12 w-12 mx-auto mb-3 text-slate-400 dark:text-gray-700" />
        <p>RiskHeatmap (D3) component renders here.</p>
        <p className="text-xs mt-1">Import <code className="text-primary">RiskHeatmap</code> from <code className="text-primary">./components/visualizations/RiskHeatmap</code></p>
      </div>
    </div>
  );
};

export default HeatmapPage;
