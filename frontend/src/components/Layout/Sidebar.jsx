import { Link, useLocation } from 'react-router-dom';
import { Home, MessageSquare, ListTree, Settings, ShieldAlert } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function Sidebar() {
  const location = useLocation();
  const { user } = useAuth();
  
  const isAdmin = user?.role === 'Admin' || user?.role === 'Super Admin';
  
  const navItems = [
    ...(isAdmin ? [{ name: 'Dashboard', path: '/dashboard', icon: <Home size={20} /> }] : []),
    { name: 'Console', path: '/chat', icon: <MessageSquare size={20} /> },
    ...(isAdmin ? [
      { name: 'Security Logs', path: '/logs', icon: <ListTree size={20} /> },
      { name: 'Settings', path: '/settings', icon: <Settings size={20} /> },
    ] : [])
  ];

  return (
    <div className="w-64 bg-slate-50 dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 h-screen flex flex-col transition-colors duration-300">
      {/* Brand */}
      <div className="h-16 flex items-center px-6 border-b border-slate-200 dark:border-slate-800">
        <ShieldAlert className="text-cyan-500 mr-3" size={24} />
        <span className="text-xl font-bold text-slate-900 dark:text-slate-100 tracking-wide">SecureShield</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-6 px-4 space-y-2">
        {navItems.map((item) => {
          const isActive = location.pathname.startsWith(item.path);
          return (
            <Link 
              key={item.name} 
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-all duration-200 ${
                isActive 
                  ? 'bg-cyan-950/50 text-cyan-400 border border-cyan-800/50' 
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:text-slate-200 hover:bg-slate-100 dark:bg-slate-800'
              }`}
            >
              {item.icon}
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* User Info Snippet */}
      <div className="p-4 border-t border-slate-200 dark:border-slate-800">
         <div className="flex items-center gap-3 px-2 py-2 rounded-lg bg-white/50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800">
           <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-cyan-500 font-bold">
             {user?.name?.charAt(0) || 'U'}
           </div>
           <div className="flex-1 min-w-0">
             <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">{user?.name}</p>
             <p className="text-xs text-slate-500 truncate">{user?.role}</p>
           </div>
         </div>
      </div>
    </div>
  );
}
