import React, { useEffect } from 'react';
import { useChatStore } from './store/chatStore';
import { useUserStore } from './store/userStore';
import Navbar from './components/Navbar';
import HomeView from './components/HomeView';
import AIChatView from './ai/AIChatView';
import DashboardView from './components/DashboardView';
import AuthModal from './components/AuthModal';
import StockPurchaseModal from './components/StockPurchaseModal';

export const App: React.FC = () => {
  const { activeTab } = useChatStore();
  const { initAuth } = useUserStore();

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-slate-900 flex flex-col font-sans selection:bg-blue-100 selection:text-blue-900">
      {/* 1. Global Navigation Bar */}
      <Navbar />

      {/* 2. Active Screen Content (Mobile & Webapp Responsive) */}
      <main className="flex-1 w-full">
        {activeTab === 'home' ? (
          <HomeView />
        ) : activeTab === 'chat' ? (
          <AIChatView />
        ) : (
          <DashboardView />
        )}
      </main>

      {/* 3. Authentication Modal */}
      <AuthModal />

      {/* 4. Stock Purchase Modal with Quantity Selector & Dummy Payment */}
      <StockPurchaseModal />
    </div>
  );
};

export default App;
