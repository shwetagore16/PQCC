import React, { useEffect, useState } from 'react';
import { devAPI } from '../api/client';

const ForecastPage: React.FC = () => {
  const [forecast, setForecast] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    devAPI.getForecast()
      .then(setForecast)
      .catch((err) => {
        console.error('Error fetching forecast:', err);
        setError(err.message);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-4">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">HNDL Exposure Forecast</h1>
      <p className="text-sm text-slate-500 dark:text-gray-400">P10/P50/P90 Prophet + Monte Carlo bands across migration scenarios</p>

      {forecast && (
        <div className="bg-white/5 backdrop-blur-sm border border-slate-200 dark:border-white/10 rounded-2xl p-5 animate-fade-in space-y-3">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Monte Carlo Summary</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            {[
              { label: 'Median exposure year', value: forecast.monte_carlo.median_exposure_year },
              { label: 'P10 (optimistic)',     value: forecast.monte_carlo.p10_exposure_year    },
              { label: 'P90 (pessimistic)',    value: forecast.monte_carlo.p90_exposure_year    },
              { label: 'P(breach ≤ 2030)',     value: `${(forecast.monte_carlo.prob_breach_before_2030 * 100).toFixed(0)}%` },
              { label: 'P(breach ≤ 2035)',     value: `${(forecast.monte_carlo.prob_breach_before_2035 * 100).toFixed(0)}%` },
            ].map(({ label, value }) => (
              <div key={label} className="bg-slate-100 dark:bg-gray-800/50 rounded-xl px-4 py-3">
                <p className="text-xs text-slate-500 mb-1">{label}</p>
                <p className="text-xl font-bold text-primary">{value}</p>
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-400 pt-2">ForecastChart (Chart.js P10/P50/P90 bands) component renders here once D3/Chart dependencies are loaded.</p>
        </div>
      )}
    </div>
  );
};

export default ForecastPage;
