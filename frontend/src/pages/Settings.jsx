import { useState } from 'react';
import { Settings2, ShieldCheck, Database, Key, Server } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function SettingsPage() {
  const { user } = useAuth();
  
  // Mock settings state
  const [layers, setLayers] = useState({
    inputGuard: true,
    policyEngine: true,
    toxicityGuard: false,
    piiGuard: true,
  });

  const toggleLayer = (layer) => {
    setLayers(prev => ({ ...prev, [layer]: !prev[layer] }));
  };

  const isAdmin = user?.role === 'Admin';

  return (
    <div className="max-w-4xl mx-auto space-y-8 bg-white dark:bg-slate-950 text-slate-800 dark:text-slate-200">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2 flex items-center gap-2">
          <Settings2 className="text-cyan-500" /> Gateway Configuration
        </h1>
        <p className="text-slate-600 dark:text-slate-400">Manage security layers, models, and API integrations.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        
        {/* Left Column: Security Layers */}
        <div className="col-span-1 md:col-span-2 space-y-6">
          
          <div className="bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
              <ShieldCheck size={20} className="text-emerald-500"/> Pipeline Layers
            </h2>
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-6">Dynamically toggle which security checks are performed during the Chain of Responsibility workflow.</p>
            
            <div className="space-y-4">
              {Object.entries(layers).map(([key, isActive]) => (
                <div key={key} className="flex items-center justify-between p-4 bg-white/50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 rounded-xl">
                  <div>
                    <h3 className="font-medium text-slate-800 dark:text-slate-200 capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}</h3>
                    <p className="text-xs text-slate-500">Evaluates payloads before LLM inference.</p>
                  </div>
                  
                  <button 
                    onClick={() => isAdmin && toggleLayer(key)}
                    disabled={!isAdmin}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${isActive ? 'bg-cyan-500' : 'bg-slate-700'}`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${isActive ? 'translate-x-6' : 'translate-x-1'}`} />
                  </button>
                </div>
              ))}
              {!isAdmin && <p className="text-xs text-rose-500 mt-2">Only System Admins can modify pipeline layers.</p>}
            </div>
          </div>

        </div>

        {/* Right Column: API & Models */}
        <div className="space-y-6">
          <div className="bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6">
             <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
              <Server size={20} className="text-purple-500"/> LLM Engine
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Provider</label>
                <select disabled={!isAdmin} className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-lg p-2.5 text-sm text-slate-800 dark:text-slate-200 outline-none disabled:opacity-50">
                  <option>Google Gemini (Current)</option>
                  <option>OpenAI API</option>
                  <option>Local Ollama</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Failover Node</label>
                <select disabled={!isAdmin} className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-lg p-2.5 text-sm text-slate-800 dark:text-slate-200 outline-none disabled:opacity-50">
                  <option>Groq API</option>
                  <option>None</option>
                </select>
              </div>
            </div>
          </div>

          <div className="bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6">
             <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
              <Database size={20} className="text-amber-500"/> Data Retention
            </h2>
            <div className="space-y-2">
               <label className="flex items-center gap-3">
                 <input type="checkbox" checked={true} readOnly className="rounded border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-cyan-500 focus:ring-cyan-500 focus:ring-offset-slate-900" />
                 <span className="text-sm text-slate-700 dark:text-slate-300">Log all failed requests</span>
               </label>
               <label className="flex items-center gap-3">
                 <input type="checkbox" checked={false} readOnly className="rounded border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-cyan-500 focus:ring-cyan-500 focus:ring-offset-slate-900" />
                 <span className="text-sm text-slate-700 dark:text-slate-300">Anonymize completely</span>
               </label>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
