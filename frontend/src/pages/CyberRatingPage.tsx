import React, { useState } from 'react';

interface AssetScore {
  url: string;
  pqcScore: number;
}

interface RatingTier {
  status: string;
  icon: string;
  range: string;
  color: string;
}

const CyberRatingPage: React.FC = () => {
  const currentScore = 755;
  const maxScore = 1000;
  const scorePercentage = (currentScore / maxScore) * 100;

  const ratingTiers: RatingTier[] = [
    { status: 'Legacy', icon: 'close', range: '< 400', color: 'bg-red-500' },
    { status: 'Standard', icon: 'warning', range: '400 till 700', color: 'bg-amber-500' },
    { status: 'Elite-PQC', icon: 'check_circle', range: '>700', color: 'bg-emerald-500' },
  ];

  const assetScores: AssetScore[] = [
    { url: 'Abc.com', pqcScore: 100 },
    { url: 'Add.com', pqcScore: 50 },
    { url: 'Acc.com', pqcScore: 0 },
  ];

  const getRatingStatus = (score: number) => {
    if (score < 400) return 'Legacy';
    if (score < 700) return 'Standard';
    return 'Elite-PQC';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Legacy':
        return 'bg-red-500';
      case 'Standard':
        return 'bg-amber-500';
      case 'Elite-PQC':
        return 'bg-emerald-500';
      default:
        return 'bg-slate-500';
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-gradient-to-b from-amber-50 to-yellow-50 dark:from-background-dark dark:to-background-dark p-8 font-display">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">Cyber Security Rating</h1>
            <p className="text-slate-600 dark:text-slate-400 text-sm mt-2">Enterprise-level cybersecurity and cryptographic posture assessment</p>
          </div>
          <div className="flex gap-2">
            <button className="px-4 py-2 rounded text-sm font-medium text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 hover:bg-white dark:hover:bg-slate-800 transition-colors flex items-center gap-2">
              <span className="material-symbols-outlined text-sm">comment</span>
              Comment
            </button>
            <button className="px-4 py-2 rounded text-sm font-medium text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 hover:bg-white dark:hover:bg-slate-800 transition-colors flex items-center gap-2">
              <span className="material-symbols-outlined text-sm">edit</span>
              Edit
            </button>
          </div>
        </div>

        {/* Main Score Card */}
        <div className="bg-gradient-to-r from-amber-700/30 to-orange-700/30 border-2 border-amber-800/40 dark:border-amber-800/30 rounded-xl p-8 shadow-lg">
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-8 underline">
            Consolidated Enterprise-Level Cyber-Rating Score
          </h2>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-4">
                <div className="text-5xl font-black text-white bg-gradient-to-br from-emerald-500 to-emerald-600 px-8 py-6 rounded-lg shadow-xl">
                  {currentScore}/{maxScore}
                </div>
                <div>
                  <div className="text-sm font-bold text-slate-700 dark:text-slate-300">Current Status</div>
                  <div className="text-lg font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
                    <span className="material-symbols-outlined text-xl">verified</span>
                    Elite-PQC
                  </div>
                  <div className="text-xs text-slate-600 dark:text-slate-400 mt-1">Indicates a stronger security posture</div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2">
              <button className="p-2 rounded border border-slate-400 dark:border-slate-600 hover:bg-white/50 dark:hover:bg-white/10 transition-colors" title="Comment">
                <span className="material-symbols-outlined text-slate-600 dark:text-slate-400">comment</span>
              </button>
              <button className="p-2 rounded border border-slate-400 dark:border-slate-600 hover:bg-white/50 dark:hover:bg-white/10 transition-colors" title="Edit">
                <span className="material-symbols-outlined text-slate-600 dark:text-slate-400">edit</span>
              </button>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mt-8 pt-8 border-t border-amber-800/30">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-700 dark:text-slate-300">OVERALL PROGRESS</span>
              <span className="text-xs font-bold text-slate-600 dark:text-slate-400">{scorePercentage.toFixed(1)}%</span>
            </div>
            <div className="h-3 bg-white/30 dark:bg-white/10 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-emerald-400 to-emerald-500 transition-all duration-500"
                style={{ width: `${scorePercentage}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Rating Scale Table */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Rating Tiers */}
          <div className="bg-white dark:bg-panel-dark rounded-lg border border-slate-200 dark:border-border-dark shadow-sm overflow-hidden">
            <div className="p-6 border-b border-slate-200 dark:border-border-dark bg-slate-50 dark:bg-black/20">
              <h3 className="font-bold text-slate-800 dark:text-slate-200">PQC Rating For Enterprise</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 dark:bg-black/20 border-b border-slate-200 dark:border-border-dark">
                    <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 border-r border-slate-200 dark:border-border-dark">Status</th>
                    <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">PQC Rating For Enterprise</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-border-dark">
                  {ratingTiers.map((tier, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-white/5 transition-colors">
                      <td className="px-6 py-4 border-r border-slate-100 dark:border-border-dark">
                        <div className="flex items-center gap-2">
                          <span className={`material-symbols-outlined text-lg ${tier.color.replace('bg-', 'text-')}`}>
                            {tier.icon}
                          </span>
                          <span className="font-bold text-slate-900 dark:text-slate-100">{tier.status}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm font-bold text-slate-900 dark:text-slate-100">{tier.range}</td>
                    </tr>
                  ))}
                  <tr className="bg-slate-100 dark:bg-black/30">
                    <td className="px-6 py-4 font-bold text-slate-900 dark:text-slate-100 border-r border-slate-200 dark:border-border-dark">Maximum Score after normalisation*</td>
                    <td className="px-6 py-4 font-bold text-slate-900 dark:text-slate-100">1000</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Asset Scores */}
          <div className="bg-white dark:bg-panel-dark rounded-lg border border-slate-200 dark:border-border-dark shadow-sm overflow-hidden">
            <div className="p-6 border-b border-slate-200 dark:border-border-dark bg-slate-50 dark:bg-black/20">
              <h3 className="font-bold text-slate-800 dark:text-slate-200">Individual Asset PQC Scores</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 dark:bg-black/20 border-b border-slate-200 dark:border-border-dark">
                    <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 border-r border-slate-200 dark:border-border-dark">URL</th>
                    <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">PQC Score</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-border-dark">
                  {assetScores.map((asset, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-white/5 transition-colors">
                      <td className="px-6 py-4 font-bold text-slate-900 dark:text-slate-100 border-r border-slate-100 dark:border-border-dark">{asset.url}</td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-4">
                          <span className="font-bold text-slate-900 dark:text-slate-100 text-lg">{asset.pqcScore}</span>
                          <div className="flex-1 bg-slate-200 dark:bg-slate-700 rounded-full h-2 max-w-xs">
                            <div
                              className={`h-full rounded-full transition-all ${
                                asset.pqcScore >= 70
                                  ? 'bg-emerald-500'
                                  : asset.pqcScore >= 40
                                  ? 'bg-amber-500'
                                  : 'bg-red-500'
                              }`}
                              style={{ width: `${asset.pqcScore}%` }}
                            ></div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Key Insights Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            {
              title: 'Security Posture',
              value: 'Elite-PQC',
              description: 'Your organization meets advanced post-quantum cryptography standards.',
              color: 'emerald',
            },
            {
              title: 'Compliance Level',
              value: '98%',
              description: 'Aligned with NIST PQC migration timeline recommendations.',
              color: 'blue',
            },
            {
              title: 'Quantum Risk Factor',
              value: 'Low',
              description: 'Minimal exposure to quantum computing threats.',
              color: 'cyan',
            },
          ].map((insight, idx) => (
            <div
              key={idx}
              className={`bg-${insight.color}-50 dark:bg-${insight.color}-950/20 border border-${insight.color}-200 dark:border-${insight.color}-800/30 rounded-lg p-6`}
            >
              <h4 className={`text-xs font-bold text-${insight.color}-600 dark:text-${insight.color}-400 uppercase tracking-wider mb-2`}>
                {insight.title}
              </h4>
              <div className={`text-2xl font-bold text-${insight.color}-700 dark:text-${insight.color}-300 mb-2`}>{insight.value}</div>
              <p className="text-sm text-slate-600 dark:text-slate-400">{insight.description}</p>
            </div>
          ))}
        </div>

        {/* Recommendations */}
        <div className="bg-white dark:bg-panel-dark rounded-lg border border-slate-200 dark:border-border-dark p-6 shadow-sm">
          <h3 className="font-bold text-slate-800 dark:text-slate-200 mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-emerald-500">lightbulb</span>
            Recommendations to Maintain Elite-PQC Status
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              '✓ Continue monitoring post-quantum algorithm implementations',
              '✓ Schedule regular cryptographic audits (quarterly)',
              '✓ Plan migration to NIST-approved PQC algorithms',
              '✓ Maintain current security practices and compliance standards',
            ].map((rec, idx) => (
              <div key={idx} className="flex items-start gap-3 p-3 rounded border border-emerald-200 dark:border-emerald-800/30 bg-emerald-50 dark:bg-emerald-950/10">
                <span className="text-emerald-600 dark:text-emerald-400 font-bold">{rec.split(' ')[0]}</span>
                <span className="text-sm text-slate-700 dark:text-slate-300">{rec.substring(2)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CyberRatingPage;
