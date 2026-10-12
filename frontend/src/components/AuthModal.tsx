import React, { useState } from 'react';
import {
  Sparkles,
  X,
  Mail,
  Lock,
  User,
  Phone,
  Eye,
  EyeOff,
  AlertCircle,
  ArrowRight,
  ShieldCheck,
  Loader2,
} from 'lucide-react';
import { useUserStore } from '../store/userStore';

export const AuthModal: React.FC = () => {
  const {
    isAuthModalOpen,
    authModalMode,
    authError,
    isLoading,
    closeAuthModal,
    setAuthModalMode,
    clearAuthError,
    login,
    signup,
  } = useUserStore();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [localValidation, setLocalValidation] = useState<string | null>(null);

  if (!isAuthModalOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalValidation(null);
    clearAuthError();

    // Client-side quick checks
    if (!email || !email.includes('@')) {
      setLocalValidation('Please enter a valid email address.');
      return;
    }

    if (!password || password.length < 6) {
      setLocalValidation('Password must be at least 6 characters.');
      return;
    }

    if (authModalMode === 'signup') {
      if (!name.trim()) {
        setLocalValidation('Please enter your full name.');
        return;
      }
      const res = await signup(name, email, password, phoneNumber || undefined);
      if (res.success) {
        setName('');
        setEmail('');
        setPassword('');
        setPhoneNumber('');
      }
    } else {
      const res = await login(email, password);
      if (res.success) {
        setEmail('');
        setPassword('');
      }
    }
  };

  const switchMode = (newMode: 'login' | 'signup') => {
    setAuthModalMode(newMode);
    setLocalValidation(null);
    clearAuthError();
  };

  const displayedError = localValidation || authError;

  return (
    <div
      className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-200"
      onClick={closeAuthModal}
    >
      <div
        className="w-full max-w-md bg-white rounded-3xl border border-slate-100 shadow-2xl overflow-hidden relative"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Header Banner */}
        <div className="p-6 md:p-8 pb-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-xs">
                <Sparkles className="w-4 h-4" />
              </div>
              <span className="text-xl font-bold tracking-tight text-slate-900">
                Growwise
              </span>
            </div>
            <button
              type="button"
              onClick={closeAuthModal}
              className="w-8 h-8 rounded-full hover:bg-slate-100 flex items-center justify-center text-slate-400 hover:text-slate-600 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <h2 className="text-xl md:text-2xl font-bold text-slate-900">
            {authModalMode === 'login' ? 'Welcome back!' : 'Create your account'}
          </h2>
          <p className="text-xs md:text-sm text-slate-500 mt-1">
            {authModalMode === 'login'
              ? 'Sign in to access your portfolio, chats, and customized goals.'
              : 'Join Growwise to chat with AI and plan your financial future.'}
          </p>

          {/* Mode Switcher Tabs */}
          <div className="mt-5 p-1 bg-slate-100/80 rounded-2xl flex items-center gap-1">
            <button
              type="button"
              onClick={() => switchMode('login')}
              className={`flex-1 py-2 text-xs md:text-sm font-semibold rounded-xl transition-all ${
                authModalMode === 'login'
                  ? 'bg-white text-blue-600 shadow-xs'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Log In
            </button>
            <button
              type="button"
              onClick={() => switchMode('signup')}
              className={`flex-1 py-2 text-xs md:text-sm font-semibold rounded-xl transition-all ${
                authModalMode === 'signup'
                  ? 'bg-white text-blue-600 shadow-xs'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Sign Up
            </button>
          </div>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="px-6 md:px-8 pb-6 space-y-4">
          {displayedError && (
            <div className="p-3 rounded-2xl bg-rose-50 border border-rose-100 flex items-start gap-2.5 text-rose-700 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{displayedError}</span>
            </div>
          )}

          {authModalMode === 'signup' && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Full Name
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  required
                  placeholder="e.g. Tanishq Sharma"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 text-xs md:text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-blue-500 focus:bg-white transition-colors"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                required
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 text-xs md:text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-blue-500 focus:bg-white transition-colors"
              />
            </div>
          </div>

          {authModalMode === 'signup' && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Mobile Number <span className="text-slate-400 font-normal">(Optional)</span>
              </label>
              <div className="relative">
                <Phone className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="tel"
                  placeholder="e.g. 9876543210"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 text-xs md:text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-blue-500 focus:bg-white transition-colors"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type={showPassword ? 'text' : 'password'}
                required
                placeholder="At least 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-10 pr-10 py-2.5 text-xs md:text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-blue-500 focus:bg-white transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="w-8 h-8 absolute right-1.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 flex items-center justify-center transition-colors"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full mt-2 py-3 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs md:text-sm shadow-sm transition-all flex items-center justify-center gap-2 disabled:opacity-60 active:scale-[0.98]"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>{authModalMode === 'login' ? 'Logging In...' : 'Creating Account...'}</span>
              </>
            ) : (
              <>
                <span>{authModalMode === 'login' ? 'Sign In to Growwise' : 'Complete Sign Up'}</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>

          <div className="pt-2 flex items-center justify-center gap-1.5 text-[11px] text-slate-400">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
            <span>Secure password encryption in MongoDB</span>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AuthModal;
