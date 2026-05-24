import { useState, useEffect } from 'react';
import api from '../api/axios';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ShieldAlert, ShieldCheck, Activity, AlertTriangle, Loader2 } from 'lucide-react';

const StatCard = ({ title, value, subValue, icon, isAlert }) => (
  <div className="p-6 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-[0_4px_20px_-10px_rgba(0,0,0,0.5)] flex flex-col h-full">
    <div className="flex justify-between items-start mb-4">
      <div className={`p-3 rounded-xl ${isAlert ? 'bg-rose-500/10 text-rose-500' : 'bg-cyan-500/10 text-cyan-500'}`}>
        {icon}
      </div>
      {subValue && <span className={`text-xs font-semibold px-2 py-1 rounded-full ${isAlert ? 'bg-rose-500/10 text-rose-400' : 'bg-emerald-500/10 text-emerald-400'}`}>{subValue}</span>}
    </div>
    <div className="mt-auto">
      <h3 className="text-slate-600 dark:text-slate-400 text-sm font-medium mb-1">{title}</h3>
      <p className="text-3xl font-bold text-slate-900 dark:text-slate-100">{value}</p>
    </div>
  </div>
);

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.get('/metrics')
      .then(res => {
        const formattedChartData = res.data.chartData?.map(item => ({
          ...item,
          time: new Date(item.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }));
        setMetrics({ ...res.data, chartData: formattedChartData });
      })
      .catch(err => {
        console.error("Failed to load metrics", err);
        setError(err.response?.status === 403 ? "Access Denied: Admin privileges required." : "Failed to load dashboard metrics.");
      });
  }, []);

  if (error) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-slate-500">
        <ShieldAlert size={48} className="text-rose-500 mb-4" />
        <p className="text-lg font-medium text-slate-900 dark:text-white">{error}</p>
        <p className="text-sm mt-2">Please navigate to the Console to use the AI Gateway.</p>
      </div>
    );
  }

  if (!metrics) {
    return <div className="h-full flex items-center justify-center"><Loader2 className="animate-spin text-cyan-500" size={32} /></div>;
  }
  return (
    <div className="max-w-7xl mx-auto flex flex-col h-full gap-6">

      {/* Header */}
      <div className="flex-none">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Systems Overview</h1>
        <p className="text-slate-600 dark:text-slate-400">Real-time monitoring of SecureShield Gateway traffic.</p>
      </div>

      {/* Top Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 flex-none">
        <StatCard title="Total Traffic" value={metrics.total.toString()} subValue="Live" icon={<Activity size={24} />} />
        <StatCard title="Safe Requests" value={metrics.safe.toString()} subValue={`${((metrics.safe / (metrics.total || 1)) * 100).toFixed(1)}%`} icon={<ShieldCheck size={24} />} />
        <StatCard title="Threats Blocked" value={metrics.blocked.toString()} subValue="Intercepted" icon={<ShieldAlert size={24} />} isAlert />
        <StatCard title="Active Rules" value={metrics.activeRules?.toString() || "0"} icon={<AlertTriangle size={24} />} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
        {/* Main Chart */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex flex-col">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-6 flex-none">Traffic & Anomalies</h2>
          <div className="flex-1 min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={metrics.chartData || []} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorSafe" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorBlocked" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="time" stroke="#64748b" tick={{ fill: '#64748b', fontSize: 12 }} tickLine={false} axisLine={false} />
                <YAxis stroke="#64748b" tick={{ fill: '#64748b', fontSize: 12 }} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px', color: '#f8fafc' }}
                  itemStyle={{ fontSize: '14px' }}
                />
                <Area type="monotone" dataKey="safe" stroke="#06b6d4" strokeWidth={3} fillOpacity={1} fill="url(#colorSafe)" />
                <Area type="monotone" dataKey="blocked" stroke="#f43f5e" strokeWidth={3} fillOpacity={1} fill="url(#colorBlocked)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Activity Feed */}
        <div className="p-6 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex flex-col">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-6">Recent Activity</h2>
          <div className="flex-1 overflow-y-auto space-y-4">

            {metrics.recentActivity && metrics.recentActivity.length > 0 ? metrics.recentActivity.map((activity) => (
              <div key={activity.id} className="flex items-start gap-4">
                <div className={`w-2 h-2 rounded-full mt-2 ${activity.isAlert ? 'bg-rose-500' : 'bg-cyan-500'}`}></div>
                <div>
                  <p className="text-sm font-medium text-slate-800 dark:text-slate-200">{activity.message}</p>
                  <p className="text-xs text-slate-500">{activity.time} • {activity.layer}</p>
                </div>
              </div>
            )) : (
              <p className="text-sm text-slate-500 italic">No recent activity found in server logs.</p>
            )}

          </div>
        </div>

      </div>

      {/* Dynamic Security Metrics */}
      {(metrics.riskDistribution || metrics.attackTrends?.length > 0 || metrics.layerStats?.length > 0) && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-none pb-6">
          {/* Risk Distribution */}
          {metrics.riskDistribution && (
            <div className="p-6 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-[0_4px_20px_-10px_rgba(0,0,0,0.5)]">
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Risk Distribution</h2>
              <div className="flex justify-between items-center text-sm px-2">
                <div className="flex flex-col items-center">
                  <span className="text-emerald-500 font-bold text-xl">{metrics.riskDistribution.LOW || 0}</span>
                  <span className="text-slate-500 font-medium text-xs mt-1">LOW</span>
                </div>
                <div className="flex flex-col items-center">
                  <span className="text-amber-500 font-bold text-xl">{metrics.riskDistribution.MEDIUM || 0}</span>
                  <span className="text-slate-500 font-medium text-xs mt-1">MEDIUM</span>
                </div>
                <div className="flex flex-col items-center">
                  <span className="text-rose-500 font-bold text-xl">{metrics.riskDistribution.HIGH || 0}</span>
                  <span className="text-slate-500 font-medium text-xs mt-1">HIGH</span>
                </div>
              </div>
            </div>
          )}

          {/* Attack Trends */}
          {metrics.attackTrends && metrics.attackTrends.length > 0 && (
            <div className="p-6 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-[0_4px_20px_-10px_rgba(0,0,0,0.5)] max-h-64 overflow-y-auto">
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Attack Trends</h2>
              <ul className="space-y-3">
                {metrics.attackTrends.map((trend, i) => (
                  <li key={i} className="flex justify-between items-center text-sm">
                    <span className="text-slate-600 dark:text-slate-400 truncate pr-2">{trend.name}</span>
                    <span className="font-semibold px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded-md text-slate-900 dark:text-slate-200 shrink-0">{trend.value}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Layer Stats */}
          {metrics.layerStats && metrics.layerStats.length > 0 && (
            <div className="p-6 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-[0_4px_20px_-10px_rgba(0,0,0,0.5)] max-h-64 overflow-y-auto">
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Layer Statistics</h2>
              <ul className="space-y-3">
                {metrics.layerStats.map((layer, i) => (
                  <li key={i} className="flex justify-between items-center text-sm">
                    <span className="text-slate-600 dark:text-slate-400 truncate pr-2">{layer.name}</span>
                    <span className="font-semibold px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded-md text-slate-900 dark:text-slate-200 shrink-0">{layer.value}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
