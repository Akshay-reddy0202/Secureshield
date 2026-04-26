import { LogOut, Bell, ShieldCheck } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { Moon, Sun } from 'lucide-react';

export default function Topbar() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="h-16 bg-white dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-6 transition-colors duration-300">
      
      {/* Left side Status */}
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-2 bg-emerald-50 dark:bg-green-950/30 text-emerald-700 dark:text-green-400 border border-emerald-200 dark:border-green-800/50 px-3 py-1.5 rounded-full text-xs font-medium tracking-wide">
          <ShieldCheck size={14} /> System Secured
        </div>
      </div>

      {/* Right side controls */}
      <div className="flex items-center gap-4">
        <button 
          onClick={toggleTheme}
          className="p-2 text-slate-600 dark:text-slate-400 hover:text-cyan-400 hover:bg-slate-50 dark:bg-slate-900 rounded-full transition-colors"
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
        
        <button className="p-2 text-slate-600 dark:text-slate-400 hover:text-cyan-400 hover:bg-slate-50 dark:bg-slate-900 rounded-full transition-colors relative">
          <Bell size={18} />
          <span className="absolute top-1 right-1 w-2 h-2 bg-rose-500 rounded-full"></span>
        </button>

        <div className="h-6 w-px bg-slate-100 dark:bg-slate-800 mx-2"></div>

        <button 
          onClick={logout}
          className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400 hover:text-rose-400 transition-colors"
        >
          <LogOut size={16} /> Logout
        </button>
      </div>
    </header>
  );
}
