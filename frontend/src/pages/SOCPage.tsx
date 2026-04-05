import React from 'react';
import { Radio } from 'lucide-react';

const SOCPage: React.FC = () => {
  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-4">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">SOC Analyst Queue</h1>
      <p className="text-sm text-slate-500 dark:text-gray-400">Real-time TLS anomaly alert stream — connect WebSocket to <code className="text-primary bg-slate-100 dark:bg-gray-800 px-1 rounded">/api/v1/compliance/ws/alerts</code></p>
      <div className="bg-white/5 backdrop-blur-sm border border-slate-200 dark:border-white/10 rounded-2xl p-8 text-center text-gray-500">
        <Radio className="h-12 w-12 mx-auto mb-3 text-slate-400 dark:text-gray-700" />
        <p>SOCAnalystQueue component renders here.</p>
        <p className="text-xs mt-1">Import <code className="text-primary">SOCAnalystQueue</code> from <code className="text-primary">./components/soc/SOCAnalystQueue</code></p>
      </div>
    </div>
  );
};

export default SOCPage;
