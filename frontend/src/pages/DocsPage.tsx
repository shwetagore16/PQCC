import React from 'react';

const DocsPage: React.FC = () => {
  return (
    <div className="flex-1 overflow-hidden flex flex-col gap-4 p-6 h-full">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">API Documentation</h1>
      <iframe
        src="http://localhost:8000/api/v1/docs"
        className="flex-1 rounded-2xl border border-slate-200 dark:border-gray-800 bg-white"
        style={{ minHeight: '60vh' }}
        title="Swagger UI"
      />
    </div>
  );
};

export default DocsPage;
