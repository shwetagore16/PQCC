import React from 'react';
import { useNavigate } from 'react-router-dom';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    // Simulate successful login
    navigate('/');
  };

  return (
    <div className="bg-background-light dark:bg-background-dark font-display flex items-center justify-center min-h-screen">
      <div className="w-full max-w-md p-6">
        {/* Logo and Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-primary/20 rounded-xl flex items-center justify-center mb-4 border border-primary/30 shadow-lg shadow-primary/10">
            <span className="material-symbols-outlined text-primary text-4xl">shield_lock</span>
          </div>
          <h1 className="text-slate-900 dark:text-slate-100 text-2xl font-bold tracking-tight text-center">
            Quantum-Safe Asset Scanner
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1 font-medium">
            Secure Asset Risk Assessment Simulator
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-white dark:bg-panel-dark border border-slate-200 dark:border-border-accent rounded-xl shadow-2xl overflow-hidden">
          {/* Card Header (Desktop App Style) */}
          <div className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-border-accent px-6 py-3 flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">System Authentication</span>
            <div className="flex gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-slate-300 dark:bg-slate-600"></div>
              <div className="w-2.5 h-2.5 rounded-full bg-slate-300 dark:bg-slate-600"></div>
            </div>
          </div>

          <form className="p-8 space-y-5" onSubmit={handleLogin}>
            {/* Username */}
            <div>
              <label className="block text-slate-700 dark:text-slate-300 text-sm font-semibold mb-1.5" htmlFor="username">
                Username
              </label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-lg">person</span>
                <input 
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-background-dark border border-slate-300 dark:border-border-accent rounded-lg text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none transition-all placeholder:text-slate-400 dark:placeholder:text-slate-600" 
                  id="username" 
                  placeholder="Enter system identifier" 
                  type="text"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="block text-slate-700 dark:text-slate-300 text-sm font-semibold" htmlFor="password">
                  Encryption Key
                </label>
                <a className="text-xs text-primary hover:underline font-medium" href="#">Reset Access</a>
              </div>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-lg">vpn_key</span>
                <input 
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-background-dark border border-slate-300 dark:border-border-accent rounded-lg text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none transition-all placeholder:text-slate-400 dark:placeholder:text-slate-600" 
                  id="password" 
                  placeholder="••••••••••••" 
                  type="password"
                />
              </div>
            </div>

            {/* Role Selection */}
            <div>
              <label className="block text-slate-700 dark:text-slate-300 text-sm font-semibold mb-1.5" htmlFor="role">
                Access Level
              </label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-lg">badge</span>
                <select 
                  className="w-full pl-10 pr-10 py-2.5 bg-slate-50 dark:bg-background-dark border border-slate-300 dark:border-border-accent rounded-lg text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none appearance-none transition-all cursor-pointer" 
                  id="role"
                  defaultValue=""
                >
                  <option disabled value="">Select Authorization Role</option>
                  <option value="admin">Administrator (Full Access)</option>
                  <option value="analyst">Security Analyst (Read/Scan Only)</option>
                </select>
                <span className="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">expand_more</span>
              </div>
            </div>

            {/* Login Button */}
            <div className="pt-2">
              <button 
                className="w-full bg-primary hover:bg-primary/90 text-white font-bold py-3 px-4 rounded-lg shadow-lg shadow-primary/20 flex items-center justify-center gap-2 transition-transform active:scale-[0.98]" 
                type="submit"
              >
                <span className="material-symbols-outlined text-lg">login</span>
                Initialize Secure Session
              </button>
            </div>
          </form>

          {/* Card Footer */}
          <div className="bg-slate-50 dark:bg-slate-800/30 px-8 py-4 border-t border-slate-200 dark:border-border-accent text-center">
            <p className="text-xs text-slate-500 dark:text-slate-500 flex items-center justify-center gap-1">
              <span className="material-symbols-outlined text-xs text-teal-accent">verified_user</span>
              FIPS 140-3 Compliance Mode Active
            </p>
          </div>
        </div>

        {/* System Footer Info --> */}
        <div className="mt-8 flex flex-col items-center gap-4">
          <div className="flex gap-6">
            <div className="flex flex-col items-center">
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-widest">Environment</span>
              <span className="text-xs font-mono text-teal-accent">PROD-X7_BETA</span>
            </div>
            <div className="w-px h-8 bg-slate-300 dark:bg-border-accent"></div>
            <div className="flex flex-col items-center">
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-widest">Uptime</span>
              <span className="text-xs font-mono text-slate-900 dark:text-slate-300">99.998%</span>
            </div>
            <div className="w-px h-8 bg-slate-300 dark:bg-border-accent"></div>
            <div className="flex flex-col items-center">
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-widest">Protocol</span>
              <span className="text-xs font-mono text-slate-900 dark:text-slate-300">QS-AES-512</span>
            </div>
          </div>
          <p className="text-[10px] text-slate-400 text-center leading-relaxed max-w-[300px]">
            Unauthorized access to this terminal is strictly prohibited and monitored by automated counter-measures.
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
