import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, ArrowRight, Lock, Eye, EyeOff } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [name, setName] = useState('');
  const [role, setRole] = useState('Employee');
  const [department, setDepartment] = useState('IOT');
  const [isLogin, setIsLogin] = useState(true);
  const { login, register, error } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if(email && password) {
      try {
        if(isLogin) {
          await login(email, password);
        } else {
          await register(email, password, name || "New User", role, department);
        }
        navigate('/dashboard'); 
      } catch (err) {
        // Error is handled by AuthContext and available in `error` variable
      }
    }
  };

  return (
    <div className="min-h-screen bg-white dark:bg-slate-950 flex flex-col md:flex-row text-slate-800 dark:text-slate-200">
      {/* Left Side: Branding & Info */}
      <div className="flex-1 bg-slate-50 dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 p-12 flex flex-col justify-center items-start relative overflow-hidden">
        {/* Decorative Grid bg */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>
        
        <div className="relative z-10 w-full max-w-lg mx-auto md:mx-0">
          <div className="mb-8 flex items-center gap-3">
            <div className="w-12 h-12 bg-cyan-900/40 rounded-xl flex items-center justify-center border border-cyan-500/30">
               <ShieldCheck className="text-cyan-400" size={28} />
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">SecureShield AI</h1>
          </div>
          <h2 className="text-4xl md:text-5xl font-bold leading-tight mb-6">
            Protecting AI interactions in <span className="text-cyan-400">real-time</span>.
          </h2>
          <p className="text-slate-600 dark:text-slate-400 text-lg mb-8 max-w-md">
            Enterprise-grade security gateway providing dynamic defense against prompt injections, PII leaks, and malicious intent.
          </p>
          <div className="space-y-4">
             <div className="flex items-center gap-3 text-slate-700 dark:text-slate-300">
               <div className="w-8 h-8 rounded-full bg-green-500/10 flex items-center justify-center"><Lock size={16} className="text-green-500"/></div>
               Role-Based Access Control
             </div>
             <div className="flex items-center gap-3 text-slate-700 dark:text-slate-300">
               <div className="w-8 h-8 rounded-full bg-purple-500/10 flex items-center justify-center"><ShieldCheck size={16} className="text-purple-500"/></div>
               Real-time Pipeline Auditing
             </div>
          </div>
        </div>
      </div>

      {/* Right Side: Form */}
      <div className="flex-1 flex items-center justify-center p-8 md:p-12 relative">
        <div className="w-full max-w-md bg-slate-50/50 dark:bg-slate-900/50 backdrop-blur-xl border border-slate-200 dark:border-slate-800 p-8 rounded-2xl shadow-2xl">
          <h3 className="text-2xl font-bold mb-2 text-slate-900 dark:text-white">{isLogin ? 'Welcome Back' : 'Create Account'}</h3>
          <p className="text-slate-600 dark:text-slate-400 mb-8">{isLogin ? 'Enter your credentials to access the console.' : 'Register a new profile and assign a role and department.'}</p>
          
          {error && (
            <div className="mb-6 p-4 bg-red-950/50 border border-red-500/30 rounded-lg text-red-400 text-sm flex items-center justify-center">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            
            {!isLogin && (
              <>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Full Name</label>
                  <input 
                    type="text" 
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700/50 rounded-lg p-3 text-slate-900 dark:text-white focus:outline-none focus:border-cyan-500 transition-colors"
                    placeholder="John Doe"
                    required={!isLogin}
                  />
                </div>
                <div className="flex gap-4">
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Role</label>
                    <select 
                      value={role}
                      onChange={(e) => setRole(e.target.value)}
                      className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700/50 rounded-lg p-3 text-slate-900 dark:text-white focus:outline-none focus:border-cyan-500 transition-colors appearance-none"
                    >
                      <option value="Employee">Employee</option>
                      <option value="Admin">Admin (Dept)</option>
                      <option value="Super Admin">Super Admin</option>
                    </select>
                  </div>
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Department</label>
                    <select 
                      value={department}
                      onChange={(e) => setDepartment(e.target.value)}
                      className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700/50 rounded-lg p-3 text-slate-900 dark:text-white focus:outline-none focus:border-cyan-500 transition-colors appearance-none"
                    >
                      <option value="Global">Global</option>
                      <option value="IOT">IOT</option>
                      <option value="Gen AI">Gen AI</option>
                      <option value="ISTM">ISTM</option>
                      <option value="PLM">PLM</option>
                    </select>
                  </div>
                </div>
              </>
            )}

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Email Address</label>
              <input 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700/50 rounded-lg p-3 text-slate-900 dark:text-white focus:outline-none focus:border-cyan-500 transition-colors"
                placeholder="analyst@secureshield.local"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Password</label>
              <div className="relative">
                <input 
                  type={showPassword ? "text" : "password"} 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700/50 rounded-lg p-3 pr-10 text-slate-900 dark:text-white focus:outline-none focus:border-cyan-500 transition-colors"
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-colors"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <button 
              type="submit" 
              className="w-full bg-cyan-600 hover:bg-cyan-500 text-slate-900 dark:text-white font-medium p-3 rounded-lg flex items-center justify-center gap-2 transition-all shadow-[0_0_15px_rgba(8,145,178,0.4)] mt-4"
            >
              {isLogin ? 'Login to Console' : 'Register Account'} <ArrowRight size={18} />
            </button>
          </form>

          <div className="mt-6 text-center">
            <button 
              onClick={() => setIsLogin(!isLogin)}
              className="text-slate-600 dark:text-slate-400 hover:text-cyan-400 text-sm font-medium transition-colors"
            >
              {isLogin ? "Don't have an account? Sign up" : "Already have an account? Log in"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
