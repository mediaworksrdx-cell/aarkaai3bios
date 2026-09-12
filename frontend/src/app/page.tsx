'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { ChatProvider, useChatContext, generateId } from '@/context/ChatContext';
import { ChatContainer } from '@/components/chat/ChatContainer';
import { Sidebar } from '@/components/sidebar/Sidebar';
import { LoginModal } from '@/components/auth/LoginModal';
import { SettingsModal } from '@/components/settings/SettingsModal';
import { getStoredToken, setStoredToken, clearToken, fetchVisitorToken } from '@/lib/api';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { User } from '@/types';

function MainChatLayout({
  user,
  setUser,
  isAnonymous,
  setIsAnonymous,
  showLoginModal,
  setShowLoginModal,
  showSettingsModal,
  setShowSettingsModal,
  handleLogout,
  handleGoogleSignIn,
  handleGitHubSignIn,
  handleContinueAsGuest
}: {
  user: User | null;
  setUser: (u: User | null) => void;
  isAnonymous: boolean;
  setIsAnonymous: (a: boolean) => void;
  showLoginModal: boolean;
  setShowLoginModal: (s: boolean) => void;
  showSettingsModal: boolean;
  setShowSettingsModal: (s: boolean) => void;
  handleLogout: () => void;
  handleGoogleSignIn: () => void;
  handleGitHubSignIn: () => void;
  handleContinueAsGuest: () => void;
}) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isMobile, setIsMobile] = useState(false);
  const [isMounted, setIsMounted] = useState(false);

  // Screen size detection — only mobile devices (< 768px) auto-close
  useEffect(() => {
    setIsMounted(true);
    const checkMobile = () => {
      if (typeof window === 'undefined') return;
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (mobile) {
        setSidebarOpen(false);
      } else {
        const savedState = localStorage.getItem('aarka-sidebar-open');
        if (savedState !== null) {
          setSidebarOpen(savedState === 'true');
        } else {
          setSidebarOpen(true);
        }
      }
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const handleToggleSidebar = useCallback(() => {
    setSidebarOpen(prev => {
      const next = !prev;
      try {
        localStorage.setItem('aarka-sidebar-open', String(next));
      } catch {}
      return next;
    });
  }, []);

  const { clearAllHistory } = useChatContext();

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[var(--bg-primary)] text-[var(--text-primary)] relative" suppressHydrationWarning>
      {/* Mobile Backdrop Overlay */}
      {isMobile && sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-30 transition-opacity duration-300"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar Container */}
      <div
        className={`
          ${isMobile ? 'fixed inset-y-0 left-0 z-40' : 'relative h-full'}
          ${sidebarOpen ? 'w-72 opacity-100' : 'w-0 opacity-0'}
          transition-all duration-300 ease-in-out overflow-hidden flex-shrink-0
        `}
      >
        <div className="w-72 h-full">
          <Sidebar
            isOpen={sidebarOpen}
            onToggle={handleToggleSidebar}
            user={user}
            onLogin={() => setShowLoginModal(true)}
            onLogout={() => {
              clearAllHistory();
              handleLogout();
            }}
            onOpenSettings={() => setShowSettingsModal(true)}
          />
        </div>
      </div>

      {/* Main Chat Workspace */}
      <main className="flex-1 flex flex-col min-w-0 h-full overflow-hidden relative">
        <ChatContainer
          onToggleSidebar={handleToggleSidebar}
          isSidebarOpen={sidebarOpen}
          user={user}
        />
      </main>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={showSettingsModal}
        onClose={() => setShowSettingsModal(false)}
        user={user}
      />

      {/* Authentication Modal */}
      <LoginModal
        isOpen={showLoginModal}
        onClose={() => {
          setShowLoginModal(false);
          setIsAnonymous(true);
        }}
        onGoogleSignIn={handleGoogleSignIn}
        onGitHubSignIn={handleGitHubSignIn}
        onContinueAsGuest={handleContinueAsGuest}
      />
    </div>
  );
}

export default function HomePage() {
  const [user, setUser] = useState<User | null>(() => {
    if (typeof window === 'undefined') return null;
    try {
      const rawUser = localStorage.getItem('aarka-user') || localStorage.getItem('aarkaa-user');
      if (rawUser && rawUser !== 'undefined' && rawUser !== 'null') {
        const parsedUser = JSON.parse(rawUser);
        if (parsedUser && typeof parsedUser === 'object') return parsedUser;
      }
      const savedAnonymous = localStorage.getItem('aarka-anonymous') || localStorage.getItem('aarkaa-anonymous');
      if (savedAnonymous === 'true') {
        return {
          id: 'guest-init',
          name: 'Guest User',
          email: 'guest@aarka-ai.com',
        };
      }
    } catch {}
    return null;
  });
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);

  // Handle OAuth callback parameters (?auth=success&token=...&name=...&email=...)
  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      const params = new URLSearchParams(window.location.search);
      if (params.get('auth') === 'success') {
        const token = params.get('token');
        const name = params.get('name') || 'Google User';
        const email = params.get('email') || 'user@aarka-ai.com';

        if (token) {
          setStoredToken(token);
        }

        const authenticatedUser: User = {
          id: generateId(),
          email,
          name,
        };

        setUser(authenticatedUser);
        localStorage.setItem('aarka-user', JSON.stringify(authenticatedUser));
        localStorage.removeItem('aarka-anonymous');
        setIsAnonymous(false);
        setShowLoginModal(false);

        // Clean query parameters from URL
        window.history.replaceState({}, document.title, window.location.pathname);
      }
    } catch (e) {
      console.warn('Error processing OAuth callback params:', e);
    }
  }, []);

  // Restore existing auth state safely
  useEffect(() => {
    try {
      const token = getStoredToken();
      const rawUser = localStorage.getItem('aarka-user') || localStorage.getItem('aarkaa-user');
      const savedAnonymous = localStorage.getItem('aarka-anonymous') || localStorage.getItem('aarkaa-anonymous');

      if (rawUser && rawUser !== 'undefined' && rawUser !== 'null') {
        try {
          const parsedUser = JSON.parse(rawUser);
          if (parsedUser && typeof parsedUser === 'object') {
            setUser(parsedUser);
            if (parsedUser.email === 'guest@aarka-ai.com') {
              setIsAnonymous(true);
            }
          }
        } catch {}
      } else if (savedAnonymous === 'true') {
        setIsAnonymous(true);
        const guestUser: User = {
          id: 'guest-' + Date.now(),
          name: 'Guest User',
          email: 'guest@aarka-ai.com',
        };
        setUser(guestUser);
        try {
          localStorage.setItem('aarka-user', JSON.stringify(guestUser));
        } catch {}
      }

      if (!token) {
        fetchVisitorToken().then((res) => {
          if (res?.access_token) {
            setStoredToken(res.access_token);
          }
        }).catch((err) => console.warn('Visitor token restore error:', err));
      }
    } catch (e) {
      console.warn('Auth state read error:', e);
    }
  }, []);

  const handleGoogleSignIn = useCallback(() => {
    if (typeof window !== 'undefined') {
      window.location.href = '/auth/google/login';
    }
  }, []);

  const handleGitHubSignIn = useCallback(() => {
    if (typeof window !== 'undefined') {
      window.location.href = '/auth/github/login';
    }
  }, []);

  const handleContinueAsGuest = useCallback(() => {
    setIsAnonymous(true);
    setShowLoginModal(false);
    try {
      localStorage.setItem('aarka-anonymous', 'true');
    } catch {}

    // Always fetch a fresh visitor token and establish guest user session
    fetchVisitorToken().then((res) => {
      if (res?.access_token) {
        setStoredToken(res.access_token);
      }
      const guestUser: User = {
        id: res?.user_id || 'guest-' + Date.now(),
        name: res?.name || 'Guest User',
        email: 'guest@aarka-ai.com',
      };
      setUser(guestUser);
      try {
        localStorage.setItem('aarka-user', JSON.stringify(guestUser));
      } catch {}
    }).catch((err) => {
      console.warn('Visitor token fetch error:', err);
      const guestUser: User = {
        id: 'guest-' + Date.now(),
        name: 'Guest User',
        email: 'guest@aarka-ai.com',
      };
      setUser(guestUser);
      try {
        localStorage.setItem('aarka-user', JSON.stringify(guestUser));
      } catch {}
    });
  }, []);

  const handleLogout = useCallback(() => {
    setUser(null);
    setIsAnonymous(false);
    clearToken();
    try {
      localStorage.removeItem('aarka-user');
      localStorage.removeItem('aarkaa-user');
      localStorage.removeItem('aarka-anonymous');
      localStorage.removeItem('aarkaa-anonymous');
      sessionStorage.removeItem('aarka-active-conv-id');
    } catch {}
  }, []);

  return (
    <ErrorBoundary>
      <ChatProvider user={user}>
        <MainChatLayout
          user={user}
          setUser={setUser}
          isAnonymous={isAnonymous}
          setIsAnonymous={setIsAnonymous}
          showLoginModal={showLoginModal}
          setShowLoginModal={setShowLoginModal}
          showSettingsModal={showSettingsModal}
          setShowSettingsModal={setShowSettingsModal}
          handleLogout={handleLogout}
          handleGoogleSignIn={handleGoogleSignIn}
          handleGitHubSignIn={handleGitHubSignIn}
          handleContinueAsGuest={handleContinueAsGuest}
        />
      </ChatProvider>
    </ErrorBoundary>
  );
}
