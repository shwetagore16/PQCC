import React, { useState } from 'react';

const ArchitectureGuidePage: React.FC = () => {
  const [activeLevel, setActiveLevel] = useState(1);

  const levels = [
    { id: 1, name: 'Level 1', title: 'Comprehensive Baseline', emoji: '🌐', color: 'from-blue-600 to-blue-400' },
    { id: 2, name: 'Level 2', title: 'CBOM Generation', emoji: '📜', color: 'from-teal-600 to-teal-400' },
    { id: 3, name: 'Level 3', title: 'Risk Scoring', emoji: '⚖️', color: 'from-amber-600 to-amber-400' },
    { id: 4, name: 'Level 4', title: 'PQC Compliance', emoji: '🔐', color: 'from-red-600 to-red-400' },
    { id: 5, name: 'Final', title: 'Cyclical Validation', emoji: '🔄', color: 'from-green-600 to-green-400' },
  ];

  const implementation: Record<number, { description: string; focus: string[]; detection: string[]; tools: string[] }> = {
    1: {
      description: 'Managing a sprawling enterprise footprint across multiple domains and ensuring the integrity of the baseline with drift detection.',
      focus: [
        'Master Asset Matrix in PostgreSQL',
        'Subdomain Enumeration with Amass/Subfinder',
        'Port scanning with Nmap',
        'Drift Detection for ghost vulnerabilities',
      ],
      detection: [
        'Real-time drift alerts on IP changes',
        'New asset discovery monitoring',
        'Decommissioned asset tracking',
      ],
      tools: ['PostgreSQL', 'Amass v4', 'Subfinder', 'Nmap 7.94'],
    },
    2: {
      description: 'Extracting deep cryptographic metadata to generate a comprehensive inventory of Algorithms, Keys, Protocols, and Certificates.',
      focus: [
        'SSLyze/testssl.sh scanner execution',
        'Cipher extraction and key exchange parsing',
        'CycloneDX v1.6 JSON generation',
        'CERT-In Annexure-A compliance',
      ],
      detection: [
        'Algorithm OIDs (name, primitive, mode, classical security level)',
        'Certificate chains and validity windows',
        'Signature algorithms and key sizes',
      ],
      tools: ['SSLyze', 'testssl.sh', 'CycloneDX', 'CERT-In schema'],
    },
    3: {
      description: 'Calculating risk scores based on control effectiveness and automating the "nightly delta" for differential analysis.',
      focus: [
        'Risk calculator function per asset',
        'Port danger scoring (21, 23, 445, 3389)',
        'Legacy TLS version penalties',
        'Cipher strength evaluation',
      ],
      detection: [
        'Score normalization: Elite (>700), Standard (400-700), Legacy (<400)',
        'Nightly CBOM delta comparison (T vs T-1)',
        'Auto-alerts for crypto downgrades',
      ],
      tools: ['Python risk engine', 'PostgreSQL', 'Celery scheduler'],
    },
    4: {
      description: 'Enforcing TLS 1.3, checking hybrid key exchanges, and issuing digital Post-Quantum Cryptography labels.',
      focus: [
        'TLS 1.3 enforcement checks',
        'Hybrid algorithm detection (Kyber + ECDH)',
        'Entropy validation (256-bit minimum)',
        'NIST PQC algorithm detection',
      ],
      detection: [
        'X25519Kyber768Draft00 (group ID 0x6399) in supported_groups',
        'ML-KEM (Kyber) OID detection',
        'ML-DSA (Dilithium) cert signature validation',
        'Auto-label: "Post Quantum Cryptography (PQC) Ready"',
      ],
      tools: ['liboqs-python', 'OpenSSL 3.x', 'NIST PQC libs'],
    },
    5: {
      description: 'Automated hygiene, differential reporting, and keeping the baseline fixed with continuous monitoring.',
      focus: [
        'Celery Beat scheduled scanning',
        'Nightly full scans (2 AM IST)',
        'On-demand scan via API triggers',
        'Differential report generation',
      ],
      detection: [
        'Hourly hygiene checks',
        'Scheduled remediation tracker',
        'Automated drift alerts',
      ],
      tools: ['Celery + Redis', 'Kafka streams', 'FastAPI scheduler'],
    },
  };

  const demoFlow = [
    '1. Open React Dashboard (blank Master Asset Matrix)',
    '2. Paste seed URL (e.g., pnb.bank.in) and click "Discover & Scan"',
    '3. Watch backend run Amass/Nmap/SSLyze in real-time',
    '4. Dashboard populates with charts and asset data',
    '5. Show auto-generated CBOM JSON file',
    '6. Click asset tagged as "Legacy" → Generate Playbook',
    '7. Show LLM-generated remediation playbook',
    '8. Highlight test server with Kyber → show "PQC-Ready" label',
  ];

  const activeContent = implementation[activeLevel];

  return (
    <div className="flex-1 overflow-hidden flex flex-col gap-6 p-8 h-full bg-gradient-to-br from-slate-50 to-slate-100 dark:from-[#0d141b] dark:to-[#1a2332]">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2 flex items-center gap-3">
          <span className="text-4xl">🏗️</span>
          Architecture & Execution Guide
        </h1>
        <p className="text-slate-600 dark:text-slate-400">Hackathon-focused implementation across 5 evaluation levels</p>
      </div>

      {/* Level Selector */}
      <div className="grid grid-cols-5 gap-3">
        {levels.map((level) => (
          <button
            key={level.id}
            onClick={() => setActiveLevel(level.id)}
            className={`p-4 rounded-lg border-2 transition-all duration-200 ${
              activeLevel === level.id
                ? `border-slate-900 dark:border-white bg-gradient-to-br ${level.color} text-white font-bold shadow-lg`
                : 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/50 text-slate-600 dark:text-slate-300 hover:border-slate-400'
            }`}
          >
            <div className="text-2xl mb-2">{level.emoji}</div>
            <div className="text-xs font-bold">{level.name}</div>
            <div className="text-[10px] opacity-75 mt-1">{level.title}</div>
          </button>
        ))}
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto grid grid-cols-2 gap-6">
        {/* Left Panel - Details */}
        <div className="bg-white dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700 p-8">
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-3">
              {levels[activeLevel - 1].emoji} {levels[activeLevel - 1].title}
            </h2>
            <p className="text-slate-600 dark:text-slate-300 leading-relaxed mb-6">{activeContent.description}</p>

            {/* Focus Areas */}
            <div className="mb-8">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-3 flex items-center gap-2">
                <span className="material-symbols-outlined text-lg">flag</span>
                Focus Areas
              </h3>
              <ul className="space-y-2">
                {activeContent.focus.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-slate-600 dark:text-slate-300">
                    <span className="text-blue-500 font-bold mt-0.5">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Detection Logic */}
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-3 flex items-center gap-2">
                <span className="material-symbols-outlined text-lg">search</span>
                Detection Logic
              </h3>
              <ul className="space-y-2">
                {activeContent.detection.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-slate-600 dark:text-slate-300">
                    <span className="text-green-500 font-bold mt-0.5">✓</span>
                    <span className="text-sm">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Right Panel - Tools & Demo */}
        <div className="space-y-6">
          {/* Tools */}
          <div className="bg-white dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-lg">build</span>
              Tech Stack
            </h3>
            <div className="flex flex-wrap gap-2">
              {activeContent.tools.map((tool, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-sm font-medium border border-blue-200 dark:border-blue-800"
                >
                  {tool}
                </span>
              ))}
            </div>
          </div>

          {/* Demo Flow */}
          <div className="bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-purple-950/20 dark:to-indigo-950/20 rounded-xl border border-purple-200 dark:border-purple-800 p-6">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-lg">play_circle</span>
              Live Demo Sequence
            </h3>
            <ol className="space-y-2">
              {demoFlow.map((step, idx) => (
                <li key={idx} className="flex items-start gap-3 text-sm text-slate-700 dark:text-slate-300">
                  <span className="font-bold text-purple-600 dark:text-purple-400 min-w-6">{idx + 1}</span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
          </div>

          {/* Key Insight */}
          <div className="bg-amber-50 dark:bg-amber-950/20 rounded-xl border border-amber-200 dark:border-amber-800 p-6">
            <h3 className="text-lg font-bold text-amber-900 dark:text-amber-100 mb-3 flex items-center gap-2">
              <span className="text-xl">💡</span>
              Key Insight
            </h3>
            {activeLevel === 1 && (
              <p className="text-sm text-amber-800 dark:text-amber-200">
                Implement "Drift Detection" to catch ghost vulnerabilities when assets are decommissioned but not removed from scans.
              </p>
            )}
            {activeLevel === 2 && (
              <p className="text-sm text-amber-800 dark:text-amber-200">
                Generate CycloneDX JSON and show judges the raw file to prove machine-readable standardization with CERT-In compliance.
              </p>
            )}
            {activeLevel === 3 && (
              <p className="text-sm text-amber-800 dark:text-amber-200">
                The "Nightly Delta" showcase is crucial—include a dashboard alert simulating a TLS downgrade detected between T-1 and T scans.
              </p>
            )}
            {activeLevel === 4 && (
              <p className="text-sm text-amber-800 dark:text-amber-200">
                Use liboqs-python to detect Kyber (0x6399 group ID in TLS ClientHello). This is the secret sauce no standard scanner has.
              </p>
            )}
            {activeLevel === 5 && (
              <p className="text-sm text-amber-800 dark:text-amber-200">
                Show Celery Beat jobs running nightly scans and Kafka streaming results to multiple consumers (CBOM, risk scorer, drift detector).
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ArchitectureGuidePage;
