import React from 'react';

const PlaceholderPage: React.FC<{ title: string }> = ({ title }) => {
  return (
    <div className="flex-1 overflow-y-auto p-6 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-slate-400 mb-2">{title}</h1>
        <p className="text-slate-500">This page is under construction based on the wireframes.</p>
      </div>
    </div>
  );
};

export default PlaceholderPage;
