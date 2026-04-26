import { useState, useEffect } from 'react';
import axios from 'axios';
import { ShieldCheck, AlertTriangle, Search, Filter, Cpu, Loader2 } from 'lucide-react';

export default function LogsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get('http://127.0.0.1:8000/logs')
      .then(res => {
        // Map raw mongo documents to UI format
        const formattedLogs = res.data.logs.map(log => {
          let layer = 'System';
          let status = 'PASSED';
          let risk = 'Low';
          let prompt = JSON.stringify(log.details);

          if (log.event.startsWith('BLOCKED_')) {
            status = 'BLOCKED';
            risk = 'High';
            layer = log.event.replace('BLOCKED_', '');
            prompt = log.details.message || prompt;
          } else if (log.event === 'SUCCESS') {
            layer = 'LLM Engine';
            prompt = log.details.response || prompt;
          } else if (log.event === 'PII_REDACTED') {
            layer = 'PII Guard';
            risk = 'Medium';
            prompt = log.details.original;
          }

          return {
            id: log.id,
            timestamp: new Date(log.timestamp).toLocaleString(),
            layer: layer,
            status: status,
            risk: risk,
            prompt: prompt,
            user: log.user_context // Keep user info for UI
          };
        });
        setLogs(formattedLogs);
      })
      .catch(err => console.error("Failed to load logs:", err))
      .finally(() => setLoading(false));
  }, []);

  const filteredLogs = logs.filter(log =>
    log.prompt.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.layer.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.user?.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.user?.department.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return <div className="h-full flex items-center justify-center bg-white dark:bg-slate-950"><Loader2 className="animate-spin text-cyan-500" size={32} /></div>;
  }

  return (
    <div className="max-w-7xl mx-auto flex flex-col h-full bg-white dark:bg-slate-950 text-slate-800 dark:text-slate-200">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2 flex items-center gap-2">
          <Cpu className="text-cyan-500" /> Security Audit Logs
        </h1>
        <p className="text-slate-600 dark:text-slate-400">Review historical payload evaluations and threat interceptions.</p>
      </div>

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
          <input
            type="text"
            placeholder="Search prompt contents or layer names..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg pl-10 pr-4 py-2.5 text-slate-800 dark:text-slate-200 focus:outline-none focus:border-cyan-500 transition-colors"
          />
        </div>
        <button className="flex items-center gap-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:bg-slate-800 px-4 py-2.5 rounded-lg transition-colors">
          <Filter size={18} /> Filter Status
        </button>
      </div>

      {/* Data Table */}
      <div className="flex-1 overflow-hidden bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl flex flex-col">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-white/50 dark:bg-slate-950/50 border-b border-slate-200 dark:border-slate-800">
                <th className="p-4 font-semibold text-slate-600 dark:text-slate-400 text-sm">Timestamp</th>
                <th className="p-4 font-semibold text-slate-600 dark:text-slate-400 text-sm">Status</th>
                <th className="p-4 font-semibold text-slate-600 dark:text-slate-400 text-sm">User Context</th>
                <th className="p-4 font-semibold text-slate-600 dark:text-slate-400 text-sm">Responsible Layer</th>
                <th className="p-4 font-semibold text-slate-600 dark:text-slate-400 text-sm">Risk Score</th>
                <th className="p-4 font-semibold text-slate-600 dark:text-slate-400 text-sm w-1/3">Payload Snapshot</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredLogs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-100/30 dark:bg-slate-800/30 transition-colors cursor-pointer">
                  <td className="p-4 text-sm font-mono text-slate-500">{log.timestamp}</td>
                  <td className="p-4">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold uppercase border ${log.status === 'PASSED' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                      }`}>
                      {log.status === 'PASSED' ? <ShieldCheck size={14} /> : <AlertTriangle size={14} />} {log.status}
                    </span>
                  </td>
                  <td className="p-4">
                    <div className="text-xs font-medium text-slate-800 dark:text-slate-200">{log.user?.email}</div>
                    <div className="text-[10px] text-slate-500 uppercase tracking-tight font-semibold">
                      {log.user?.role} • {log.user?.department}
                    </div>
                  </td>
                  <td className="p-4 text-sm text-cyan-400 font-medium">{log.layer}</td>
                  <td className="p-4">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${log.risk === 'High' ? 'text-rose-400 bg-rose-500/10' : log.risk === 'Medium' ? 'text-amber-400 bg-amber-500/10' : 'text-emerald-400 bg-emerald-500/10'
                      }`}>
                      {log.risk}
                    </span>
                  </td>
                  <td className="p-4 text-sm text-slate-700 dark:text-slate-300 truncate max-w-[200px]">{log.prompt}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {filteredLogs.length === 0 && (
            <div className="p-8 text-center text-slate-500">No audit logs match your search.</div>
          )}
        </div>
      </div>
    </div>
  );
}
