import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, AlertTriangle, ShieldCheck, Trash2 } from 'lucide-react';
import { motion } from 'framer-motion';

export default function ChatBox({ messages, onSendMessage, onClearHistory, loading }) {
  const [input, setInput] = useState('');
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if(input.trim()) {
      onSendMessage(input);
      setInput('');
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-white dark:bg-slate-950 relative">
      {/* Header with Clear Action */}
      <div className="h-14 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-6 bg-white/50 dark:bg-slate-950/50 backdrop-blur-md z-10">
        <div className="flex items-center gap-2">
          <ShieldCheck className="text-cyan-500" size={18} />
          <span className="text-sm font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">Security Console</span>
        </div>
        {messages.length > 0 && (
          <button 
            onClick={onClearHistory}
            className="flex items-center gap-2 text-xs font-medium text-slate-500 hover:text-rose-500 transition-colors"
            title="Clear Chat History"
          >
            <Trash2 size={14} />
            <span>Clear History</span>
          </button>
        )}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-slate-500">
            <ShieldCheck size={48} className="text-slate-800 mb-4" />
            <p className="text-lg">Send a prompt. SecureShield will analyze it.</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            key={idx} 
            className={`flex flex-col max-w-[85%] ${msg.role === 'user' ? 'self-end items-end ml-auto' : 'self-start items-start'}`}
          >
            {/* Metadata Badge */}
            {msg.role === 'system' && (
              <div className={`flex items-center gap-1.5 text-xs font-semibold uppercase px-2.5 py-1 rounded-t-lg border-x border-t mb-[-1px] ${
                msg.status === 'PASSED' 
                  ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30' 
                  : 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30'
              }`}>
                {msg.status === 'PASSED' ? <ShieldCheck size={12}/> : <AlertTriangle size={12}/>}
                {msg.status}
              </div>
            )}

            {/* Bubble */}
            <div className={`p-4 rounded-2xl shadow-sm border ${
              msg.role === 'user' 
                ? 'bg-cyan-600/10 text-cyan-900 dark:text-cyan-50 border-cyan-500/20 rounded-tr-sm' 
                : msg.status === 'PASSED'
                  ? 'bg-slate-50 dark:bg-slate-900 border-emerald-500/20 text-slate-800 dark:text-slate-200 rounded-tl-sm'
                  : 'bg-rose-50/50 dark:bg-rose-950/20 border-rose-500/30 text-rose-800 dark:text-rose-200 rounded-tl-sm'
            }`}>
              <p className="whitespace-pre-wrap leading-relaxed whitespace-pre-line">{msg.content}</p>
            </div>
            
            {/* Footer details (if blocked) */}
            {msg.role === 'system' && msg.reason && (
               <p className="text-xs text-rose-500 dark:text-rose-400 mt-2 ml-2 flex items-center gap-1">
                 <AlertTriangle size={12}/> Blocked Reason: {msg.reason}
               </p>
            )}
          </motion.div>
        ))}
        {loading && (
           <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-3 text-cyan-600 dark:text-cyan-500 self-start p-4 bg-slate-50 dark:bg-slate-900 rounded-2xl rounded-tl-sm border border-slate-200 dark:border-slate-800">
             <Loader2 size={18} className="animate-spin" /> Analyzing payload through pipeline...
           </motion.div>
        )}
        <div ref={endRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950/80 backdrop-blur-md">
        <form onSubmit={handleSubmit} className="relative flex items-center max-w-4xl mx-auto">
          <input 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            placeholder="Test a payload or prompt..."
            className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl py-4 pl-4 pr-16 text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all disabled:opacity-50"
          />
          <button 
            type="submit"
            disabled={!input.trim() || loading}
            className="absolute right-2 p-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:bg-slate-200 dark:disabled:bg-slate-800 disabled:text-slate-400 dark:disabled:text-slate-500"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}
