import React, { useState } from 'react';

const SettingsPage: React.FC = () => {
  const [darkTheme, setDarkTheme] = useState(true);
  const [notifications, setNotifications] = useState(true);

  return (
    <div className="flex-1 overflow-y-auto bg-background-light dark:bg-background-dark p-8 font-display">
      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-black text-slate-900 dark:text-slate-100 tracking-tight">System Settings</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">Configure global application preferences and security policies.</p>
        </div>

        <div className="grid grid-cols-1 gap-6">
          {/* General Settings */}
          <div className="bg-white dark:bg-panel-dark border border-slate-200 dark:border-border-accent rounded-xl p-6 shadow-sm">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-6 flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">settings_applications</span>
              General Preferences
            </h3>
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-bold text-slate-800 dark:text-slate-200">Dark Mode Interface</p>
                  <p className="text-xs text-slate-500">Enable high-contrast dark theme for low-light environments.</p>
                </div>
                <button 
                  onClick={() => setDarkTheme(!darkTheme)}
                  className={`w-12 h-6 rounded-full transition-colors relative ${darkTheme ? 'bg-primary' : 'bg-slate-300 dark:bg-slate-700'}`}
                >
                  <div className={`absolute top-1 size-4 rounded-full bg-white transition-all ${darkTheme ? 'left-7' : 'left-1'}`}></div>
                </button>
              </div>
              <div className="border-t border-slate-100 dark:border-border-accent pt-6 flex items-center justify-between">
                <div>
                  <p className="text-sm font-bold text-slate-800 dark:text-slate-200">System Notifications</p>
                  <p className="text-xs text-slate-500">Receive real-time alerts for scan completions and security threats.</p>
                </div>
                <button 
                  onClick={() => setNotifications(!notifications)}
                  className={`w-12 h-6 rounded-full transition-colors relative ${notifications ? 'bg-primary' : 'bg-slate-300 dark:bg-slate-700'}`}
                >
                  <div className={`absolute top-1 size-4 rounded-full bg-white transition-all ${notifications ? 'left-7' : 'left-1'}`}></div>
                </button>
              </div>
            </div>
          </div>

          {/* Security & API */}
          <div className="bg-white dark:bg-panel-dark border border-slate-200 dark:border-border-accent rounded-xl p-6 shadow-sm">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-6 flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">security</span>
              Security & API Access
            </h3>
            <div className="space-y-4">
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-2">API Endpoint URL</label>
                <input 
                  defaultValue="http://localhost:8000"
                  className="w-full bg-slate-50 dark:bg-background-dark border border-slate-200 dark:border-border-accent rounded p-2.5 text-sm focus:ring-1 focus:ring-primary outline-none text-slate-900 dark:text-slate-100 font-mono"
                  type="text"
                />
              </div>
              <div className="pt-2">
                <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-2">Authentication Token</label>
                <div className="flex gap-2">
                  <input 
                    readOnly
                    type="password"
                    defaultValue="token_placeholder_change_me"
                    className="flex-1 bg-slate-50 dark:bg-background-dark border border-slate-200 dark:border-border-accent rounded p-2.5 text-sm outline-none text-slate-500 font-mono"
                  />
                  <button className="px-4 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-border-accent rounded text-xs font-bold hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">
                    Regenerate
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Danger Zone */}
          <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 rounded-xl p-6 shadow-sm">
            <h3 className="text-sm font-bold uppercase tracking-wider text-red-600 dark:text-red-400 mb-6 flex items-center gap-2">
              <span className="material-symbols-outlined">dangerous</span>
              Danger Zone
            </h3>
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <p className="text-sm font-bold text-red-700 dark:text-red-300">Reset System Database</p>
                <p className="text-xs text-red-600/70 dark:text-red-400/60">Permanently delete all assets, scan history, and user data. This cannot be undone.</p>
              </div>
              <button className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white font-bold text-xs rounded shadow-lg shadow-red-600/20 transition-all active:scale-95">
                Reset All Data
              </button>
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-4 pb-12">
          <button className="px-8 py-2.5 bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded font-bold text-sm hover:brightness-110 transition-all">
            Discard Changes
          </button>
          <button className="px-8 py-2.5 bg-primary text-white rounded font-bold text-sm shadow-xl shadow-primary/20 hover:brightness-110 active:scale-95 transition-all">
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
