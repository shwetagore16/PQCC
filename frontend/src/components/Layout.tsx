import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';

const Layout: React.FC = () => {
  const location = useLocation();

  const navItems = [
    { name: 'Dashboard', icon: 'dashboard', path: '/' },
    { name: 'Asset Management', icon: 'inventory_2', path: '/assets' },
    { name: 'Run Scan', icon: 'play_circle', path: '/scan' },
    { name: 'Scan Results', icon: 'receipt_long', path: '/results' },
    { name: 'CBOM Records', icon: 'list_alt', path: '/cbom' },
    { name: 'Risk Analysis', icon: 'report_problem', path: '/risk' },
    { name: 'PQC Classification', icon: 'category', path: '/pqc' },
    { name: 'Cyber Rating', icon: 'shield', path: '/cyber-rating' },
    { name: 'Reports', icon: 'bar_chart', path: '/reports' },
  ];

  const docItems = [
    { name: 'Tech Guide (Modules)', icon: 'auto_stories', path: '/tech-guide' },
    { name: 'Architecture Guide', icon: 'architecture', path: '/architecture' },
  ];

  return (
    <div className="flex h-screen w-full bg-background-light dark:bg-background-dark text-slate-900 dark:text-slate-100 overflow-hidden font-display">
      {/* Sidebar Navigation */}
      <aside className="w-64 flex flex-col bg-slate-100 dark:bg-background-dark border-r border-slate-200 dark:border-slate-800">
        <div className="p-6 flex items-center gap-3">
          <div className="size-10 bg-primary rounded-lg flex items-center justify-center text-white">
            <span className="material-symbols-outlined text-2xl">shield_lock</span>
          </div>
          <div className="flex flex-col">
            <h1 className="text-sm font-bold tracking-tight uppercase text-primary">Quantum-Safe</h1>
            <p className="text-[10px] text-slate-500 dark:text-slate-400 font-medium tracking-widest">ASSET SCANNER</p>
          </div>
        </div>

        <nav className="flex-1 px-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <Link
              key={item.name}
              to={item.path}
              className={`flex items-center gap-3 px-3 py-2 rounded transition-colors ${
                location.pathname === item.path
                  ? 'bg-primary text-white'
                  : 'text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800'
              }`}
            >
              <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
              <span className="text-sm font-medium">{item.name}</span>
            </Link>
          ))}
          
          <div className="mt-6 border-t border-slate-200 dark:border-slate-800 pt-4">
            <div className="px-3 py-2 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Documentation</div>
            {docItems.map((item) => (
              <Link
                key={item.name}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2 rounded transition-colors ${
                  location.pathname === item.path
                    ? 'bg-primary text-white'
                    : 'text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800'
                }`}
              >
                <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
                <span className="text-sm font-medium">{item.name}</span>
              </Link>
            ))}
          </div>
          
          <div className="mt-8 border-t border-slate-200 dark:border-slate-800 pt-4">
            <Link to="/users" className="flex items-center gap-3 px-3 py-2 rounded text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors">
              <span className="material-symbols-outlined text-[20px]">group</span>
              <span className="text-sm font-medium">User Management</span>
            </Link>
            <Link to="/settings" className="flex items-center gap-3 px-3 py-2 rounded text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors">
              <span className="material-symbols-outlined text-[20px]">settings</span>
              <span className="text-sm font-medium">Settings</span>
            </Link>
            <button className="w-full flex items-center gap-3 px-3 py-2 rounded text-red-500 hover:bg-red-50 dark:hover:bg-red-900/10 transition-colors">
              <span className="material-symbols-outlined text-[20px]">logout</span>
              <span className="text-sm font-medium">Logout</span>
            </button>
          </div>
        </nav>

        <div className="p-4 bg-slate-200/50 dark:bg-slate-800/50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-primary/20 flex items-center justify-center text-primary font-bold text-xs">JD</div>
            <div className="flex-1 overflow-hidden">
              <p className="text-xs font-semibold truncate text-slate-900 dark:text-slate-100">John Doe</p>
              <p className="text-[10px] text-slate-500 truncate">Security Architect</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0 bg-slate-50 dark:bg-[#0d141b]">
        {/* Top Header */}
        <header className="h-16 flex items-center justify-between px-6 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-background-dark shrink-0">
          <div className="flex items-center gap-4 flex-1 max-w-xl">
            <div className="relative w-full">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-lg">search</span>
              <input 
                className="w-full bg-slate-100 dark:bg-slate-800/50 border-none rounded-lg pl-10 pr-4 py-2 text-sm focus:ring-2 focus:ring-primary/40 transition-all text-slate-900 dark:text-slate-100" 
                placeholder="Search assets, scans, or reports..." 
                type="text"
              />
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button className="p-2 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg relative">
              <span className="material-symbols-outlined">notifications</span>
              <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-white dark:border-background-dark"></span>
            </button>
            <button className="p-2 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg">
              <span className="material-symbols-outlined">help_outline</span>
            </button>
            <div className="h-8 w-px bg-slate-200 dark:border-slate-800 mx-2"></div>
            <div className="size-8 rounded-full overflow-hidden bg-slate-200 ring-2 ring-primary/20">
              <img 
                alt="Profile" 
                className="w-full h-full object-cover" 
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuAKYw4oR8B29I9YWP_HSc7OmQbOoSrDqP0uI4T-kVT_GiyEI3qg7Nv1sXCqd1PPFkxC-xiUzDmC7tKCElZr7CxwLVpM2hldJ8xK5kMCfc7G99wOsZKe05bWMA6AL2rWGEaCRyN35zQjbW574qdaUvc1LXKzeuwBB1do74gddG9pV-MCELbrygZJFn_jtwKoi9OQ3GwG72j26qyveYj04TP7fa98-1Mozvr5rpRoSCK1mhlt2mlzicEKSgz_YL3Ruf3VC7TU_j-5Xm4"
              />
            </div>
          </div>
        </header>

        {/* Dashboard Content */}
        <Outlet />

        {/* Footer / System Bar */}
        <footer className="h-8 bg-slate-100 dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between px-6 shrink-0">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-green-500"></span>
              <span className="text-[10px] font-bold text-slate-500 dark:text-slate-400">SYSTEM: OPERATIONAL</span>
            </div>
            <div className="h-3 w-px bg-slate-300 dark:bg-slate-700"></div>
            <span className="text-[10px] text-slate-500">Scanner Engine v2.4.12</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-[10px] text-slate-500 uppercase tracking-widest font-medium">Quantum-Safe Asset Management System © 2024</span>
          </div>
        </footer>
      </main>
    </div>
  );
};

export default Layout;
