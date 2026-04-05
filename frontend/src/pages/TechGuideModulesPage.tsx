import React, { useState } from 'react';

const TechGuideModulesPage: React.FC = () => {
  const [activeModule, setActiveModule] = useState(1);

  const modules = [
    {
      id: 1,
      name: 'Asset Discovery',
      emoji: '🔍',
      color: 'from-blue-600 to-blue-400',
      icon: 'network_check',
    },
    {
      id: 2,
      name: 'Baseline & Topology',
      emoji: '🗺',
      color: 'from-teal-600 to-teal-400',
      icon: 'account_tree',
    },
    {
      id: 3,
      name: 'Scan Orchestration',
      emoji: '⚙️',
      color: 'from-purple-600 to-purple-400',
      icon: 'tune',
    },
    {
      id: 4,
      name: 'CBOM & Crypto',
      emoji: '📋',
      color: 'from-amber-600 to-amber-400',
      icon: 'description',
    },
    {
      id: 5,
      name: 'PQC Readiness',
      emoji: '🛡',
      color: 'from-green-600 to-green-400',
      icon: 'security',
    },
    {
      id: 6,
      name: 'Dashboard & Remediation',
      emoji: '📊',
      color: 'from-red-600 to-red-400',
      icon: 'dashboard',
    },
    {
      id: 7,
      name: 'Continuous Monitoring',
      emoji: '🔄',
      color: 'from-orange-600 to-orange-400',
      icon: 'history',
    },
    {
      id: 8,
      name: 'PQC Algorithms',
      emoji: '🔬',
      color: 'from-indigo-600 to-indigo-400',
      icon: 'science',
    },
    {
      id: 9,
      name: 'Banking Benchmarks',
      emoji: '🏦',
      color: 'from-cyan-600 to-cyan-400',
      icon: 'business',
    },
    {
      id: 10,
      name: 'Scalability',
      emoji: '⚡',
      color: 'from-pink-600 to-pink-400',
      icon: 'flash_on',
    },
  ];

  const content: Record<number, { title: string; description: string; tools: string[]; aiComponents: string[]; highlights: string[] }> = {
    1: {
      title: 'Asset Discovery',
      description: 'Discover every public-facing PNB asset using passive OSINT and active enumeration, normalized into a Master Asset Matrix.',
      tools: ['Amass v4', 'Subfinder', 'dnsx', 'Shodan API', 'Censys API', 'Masscan', 'Nmap 7.94', 'CertStream'],
      aiComponents: ['NLP — CT Log Parsing (spaCy)', 'Isolation Forest — IP Range Clustering', 'FastText — Subdomain Classification', 'Random Forest — Asset Type Classifier'],
      highlights: ['Real-time certificate monitoring via Certstream', 'FastText model for 95%+ subdomain classification accuracy', 'DBSCAN for shadow IT detection via IP clustering'],
    },
    2: {
      title: 'Baseline & Topology Intelligence',
      description: 'Build a living topological graph of assets with ownership, dependencies, and real-time drift detection.',
      tools: ['Neo4j 5.x', 'PostgreSQL 15', 'py2neo', 'NetworkX', 'D3.js', 'Redis'],
      aiComponents: ['PyTorch Geometric (GNN)', 'Node2Vec — Asset Embeddings', 'GraphSAGE — Topology Classification', 'LSTM — Lifecycle Prediction'],
      highlights: ['Neo4j graph schema with attack path queries', 'GraphSAGE propagates risk across topology', 'Drift detection with Isolation Forest'],
    },
    3: {
      title: 'Scan Orchestration & Crypto Inspection',
      description: 'Active TLS handshake probing, cipher extraction, certificate chain analysis, and quantum-vulnerability detection.',
      tools: ['SSLyze 5.x', 'testssl.sh', 'ZGrab2', 'tlsx', 'JARM', 'JA3/JA3S'],
      aiComponents: ['XGBoost Cipher Scorer', 'One-Class SVM for novel ciphers', 'JARM hash database matching'],
      highlights: ['Detects legacy protocols (SSLv3, TLS 1.0/1.1)', 'JARM fingerprinting identifies server software', 'Auto-detection of quantum-vulnerable key exchanges'],
    },
    4: {
      title: 'CBOM & Crypto Intelligence',
      description: 'Generate CERT-In compliant Cryptographic Bill of Materials with algorithm inventory and agility scoring.',
      tools: ['CycloneDX v1.6', 'cyclonedx-python-lib', 'cdxgen', 'PostgreSQL'],
      aiComponents: ['LLM Summarization (Claude)', 'NLP — Certificate Field Extraction', 'Crypto Agility Score ML'],
      highlights: ['Dynamic CBOM delta comparison with natural language explanations', 'HNDL Exposure Window calculation per asset', 'Agility Score = 5-factor ML model'],
    },
    5: {
      title: 'PQC Readiness & Risk Scoring',
      description: 'Validate NIST FIPS 203/204/205 compliance, assign PQC labels, calculate HNDL urgency with AI explainability.',
      tools: ['liboqs-python', 'NIST PQC libs', 'ML-KEM (Kyber)', 'ML-DSA (Dilithium)', 'SPHINCS+'],
      aiComponents: ['XGBoost Risk Scorer + SHAP', 'PyTorch GNN Attack Path', 'Monte Carlo HNDL Probability'],
      highlights: ['Mosca\'s Theorem HNDL calculator (10-15 year CRQC estimate)', 'Auto-labels: PQC-READY / Standard / Legacy / Critical', 'SHAP explains every risk point deduction'],
    },
    6: {
      title: 'Dashboard & Remediation',
      description: 'Enterprise React SOC console with RBAC, AI-driven playbooks, compliance validation, and report generation.',
      tools: ['React 18', 'Tailwind CSS', 'D3.js', 'Recharts', 'Keycloak RBAC', 'Slack webhooks'],
      aiComponents: ['LangChain RAG Playbook Engine', 'Claude API NL Recommendations', 'ChromaDB Knowledge Base'],
      highlights: ['Auto-generated remediation playbooks from CBOM + risk', 'Real-time topology attack path visualization', 'Human-in-the-loop approval for critical actions'],
    },
    7: {
      title: 'Continuous Monitoring',
      description: 'Nightly scans, baseline comparison, drift alerting, forecasting, and adaptive rule learning.',
      tools: ['Celery + Redis', 'Apache Kafka', 'Facebook Prophet', 'PyTorch LSTM'],
      aiComponents: ['Prophet Migration Timeline Forecasting', 'LSTM Anomaly Detection', 'Online Learning Rule Feedback'],
      highlights: ['Prophet forecasts PQC migration completion date', 'LSTM autoencoder catches gradual cipher downgrades', 'Analyst feedback auto-tunes model weights'],
    },
    8: {
      title: 'PQC Algorithms Deep Dive',
      description: 'Algorithm-by-algorithm analysis with OIDs, detection logic, and quantum-vulnerability mappings.',
      tools: ['liboqs-python', 'OpenSSL 3.x', 'NIST standards'],
      aiComponents: ['Algorithm OID matching', 'Hybrid key exchange detection'],
      highlights: ['ML-KEM (Kyber) OID detection in TLS', 'ML-DSA (Dilithium) cert signature validation', 'X25519Kyber768 hybrid mode detection'],
    },
    9: {
      title: 'What Leading Banks Do',
      description: 'Competitive benchmarking against JP Morgan (Axonius), HSBC (ServiceNow), Goldman Sachs, Citi, and others.',
      tools: ['Industry tools comparison', 'IDRBT/RBI compliance'],
      aiComponents: ['PQC migration benchmarks'],
      highlights: ['ING Bank Kyber pilot detection', 'JPMorgan X25519Kyber768 tracking', 'CERT-In compliance alignment'],
    },
    10: {
      title: 'Scalability & Production Architecture',
      description: 'Kubernetes deployment, data pipeline optimization, ML model serving, and security hardening.',
      tools: ['Kubernetes', 'FastAPI', 'PostgreSQL', 'Redis Cluster', 'Neo4j Enterprise'],
      aiComponents: ['TorchServe model serving', 'MLflow version control'],
      highlights: ['10K+ assets per scan cycle', '<60s alert latency', '99.9% uptime SLA', 'Horizontal scaling with HPA'],
    },
  };

  const activeContent = content[activeModule];

  return (
    <div className="flex-1 overflow-hidden flex flex-col gap-6 p-8 h-full bg-gradient-to-br from-slate-50 to-slate-100 dark:from-[#0d141b] dark:to-[#1a2332]">
      {/* Header */}
      <div className="flex items-start justify-between gap-6">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2 flex items-center gap-3">
            <span className="text-4xl">📚</span>
            QShieldX Technical Guide
          </h1>
          <p className="text-slate-600 dark:text-slate-400">Deep-dive into each module of the PQC security platform</p>
        </div>
      </div>

      {/* Module Selector */}
      <div className="grid grid-cols-5 gap-3 max-h-[120px] overflow-y-auto">
        {modules.map((module) => (
          <button
            key={module.id}
            onClick={() => setActiveModule(module.id)}
            className={`p-4 rounded-lg border-2 transition-all duration-200 text-center ${
              activeModule === module.id
                ? `border-slate-900 dark:border-white bg-gradient-to-br ${module.color} text-white font-bold shadow-lg`
                : 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/50 text-slate-600 dark:text-slate-300 hover:border-slate-400 dark:hover:border-slate-500'
            }`}
          >
            <div className="text-xl mb-1">{module.emoji}</div>
            <div className="text-xs font-semibold line-clamp-2">{module.name}</div>
          </button>
        ))}
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto bg-white dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700 p-8">
        <div className="max-w-4xl">
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-3 flex items-center gap-3">
              <span className="text-3xl">{modules[activeModule - 1].emoji}</span>
              {activeContent.title}
            </h2>
            <p className="text-slate-600 dark:text-slate-300 leading-relaxed">{activeContent.description}</p>
          </div>

          {/* Core Tools */}
          <div className="mb-8">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined">build</span>
              Core Tools & Technologies
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

          {/* AI/ML Components */}
          <div className="mb-8">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined">psychology</span>
              AI/ML Components
            </h3>
            <div className="flex flex-wrap gap-2">
              {activeContent.aiComponents.map((comp, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 text-sm font-medium border border-purple-200 dark:border-purple-800"
                >
                  {comp}
                </span>
              ))}
            </div>
          </div>

          {/* Key Highlights */}
          <div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined">lightbulb</span>
              Key Highlights & Differentiators
            </h3>
            <ul className="space-y-2">
              {activeContent.highlights.map((highlight, idx) => (
                <li key={idx} className="flex items-start gap-3 text-slate-600 dark:text-slate-300">
                  <span className="text-green-500 font-bold mt-1">✓</span>
                  <span>{highlight}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TechGuideModulesPage;
