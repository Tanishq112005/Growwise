import React, { useState, useRef, useEffect } from 'react';
import { Bell, Sparkles, LogOut } from 'lucide-react';
import { useChatStore } from '../store/chatStore';
import { useUserStore } from '../store/userStore';

export const Navbar: React.FC = () => {
  const { activeTab, setActiveTab } = useChatStore();
  const { user, isAuthenticated, openAuthModal, logout } = useUserStore();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="w-full bg-white border-b border-slate-100 sticky top-0 z-30">
      <div className="max-w-6xl mx-auto px-4 md:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo */}
        <div className="flex items-center gap-2 cursor-pointer" onClick={() => setActiveTab('home')}>
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-xs">
            <Sparkles className="w-4 h-4" />
          </div>
          <span className="hidden sm:inline text-lg md:text-xl font-bold tracking-tight text-slate-900">
            Growwise
          </span>
        </div>

        {/* Center Navigation Tabs */}
        <nav className="flex items-center gap-1 md:gap-6">
          {(
            [
              { id: 'home' as const, label: 'Home' },
              { id: 'dashboard' as const, label: 'Dashboard' },
              { id: 'chat' as const, label: 'AI Chat' },
            ]
          ).map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`relative py-5 px-2 md:px-3 text-xs md:text-sm font-semibold transition-colors ${
                activeTab === tab.id
                  ? 'text-blue-600'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              {tab.id === 'chat' ? (
                <>
                  <span className="sm:hidden">Chat</span>
                  <span className="hidden sm:inline">{tab.label}</span>
                </>
              ) : (
                tab.label
              )}
              {activeTab === tab.id && (
                <span className="absolute bottom-0 left-0 w-full h-0.5 bg-blue-600 rounded-t-full"></span>
              )}
            </button>
          ))}
        </nav>

        {/* Right Utility: Auth Buttons / User Profile */}
        <div className="flex items-center gap-2 md:gap-3">
          <button
            type="button"
            aria-label="Notifications"
            className="hidden md:flex w-9 h-9 rounded-full hover:bg-slate-100 items-center justify-center text-slate-500 transition-colors"
          >
            <Bell className="w-4 h-4" />
          </button>

          {!isAuthenticated ? (
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => openAuthModal('login')}
                className="hidden sm:inline-flex px-3 md:px-3.5 py-1.5 rounded-xl border border-slate-200 hover:border-slate-300 text-slate-700 font-semibold text-xs transition-colors hover:bg-slate-50"
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => openAuthModal('signup')}
                className="px-3 md:px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-xs transition-all active:scale-95"
              >
                Sign Up
              </button>
            </div>
          ) : (
            <div className="relative" ref={menuRef}>
              <button
                type="button"
                onClick={() => setMenuOpen(!menuOpen)}
                className="flex items-center gap-2 p-1 pl-2 rounded-2xl hover:bg-slate-50 border border-slate-100 transition-colors"
              >
                <span className="hidden md:inline-block text-xs font-semibold text-slate-700 max-w-[120px] truncate">
                  {user?.name || 'Account'}
                </span>
                <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white font-bold text-xs shadow-xs">
                  {user?.name ? user.name.charAt(0).toUpperCase() : 'U'}
                </div>
              </button>

              {/* Profile Dropdown */}
              {menuOpen && (
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-2xl shadow-xl border border-slate-100 py-2 z-50 animate-in fade-in zoom-in-95 duration-150">
                  <div className="px-4 py-2 border-b border-slate-100">
                    <p className="text-xs font-bold text-slate-900 truncate">
                      {user?.name}
                    </p>
                    <p className="text-[11px] text-slate-500 truncate mt-0.5">
                      {user?.email}
                    </p>
                    <p className="text-[10px] text-slate-400 mt-1 font-mono truncate">
                      ID: {user?.user_id?.slice(0, 8)}...
                    </p>
                  </div>

                  <div className="p-1">
                    <button
                      type="button"
                      onClick={() => {
                        setMenuOpen(false);
                        logout();
                      }}
                      className="w-full flex items-center gap-2 px-3 py-2 text-xs font-semibold text-rose-600 hover:bg-rose-50 rounded-xl transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Log Out</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Navbar;
