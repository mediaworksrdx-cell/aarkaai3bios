'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';

type Theme = 'dark' | 'light';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

/**
 * Apply theme classes and data attributes to the document.
 * This function is safe to call during SSR (no-op) and CSR.
 */
function applyThemeToDOM(t: Theme) {
  if (typeof document === 'undefined') return;
  const root = document.documentElement;
  const body = document.body;

  // Set classes
  root.classList.remove('dark', 'light');
  root.classList.add(t);
  root.setAttribute('data-theme', t);

  // Also set on body for full coverage
  if (body) {
    body.classList.remove('dark', 'light');
    body.classList.add(t);
    body.setAttribute('data-theme', t);
  }
}

/**
 * Read the stored theme from localStorage, defaulting to 'dark'.
 */
function getStoredTheme(): Theme {
  if (typeof window === 'undefined') return 'dark';
  try {
    const saved = localStorage.getItem('aarka-theme') || localStorage.getItem('aarkaa-theme');
    if (saved === 'light' || saved === 'dark') return saved;
  } catch {}
  return 'dark';
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => getStoredTheme());
  const [mounted, setMounted] = useState(false);

  // Apply theme immediately on first client render
  useEffect(() => {
    const initial = getStoredTheme();
    setThemeState(initial);
    applyThemeToDOM(initial);
    setMounted(true);
  }, []);

  const setTheme = useCallback((t: Theme) => {
    setThemeState(t);
    try {
      localStorage.setItem('aarka-theme', t);
      localStorage.setItem('aarkaa-theme', t);
    } catch {}
    applyThemeToDOM(t);
  }, []);

  const toggleTheme = useCallback(() => {
    setThemeState(prev => {
      const next = prev === 'dark' ? 'light' : 'dark';
      try {
        localStorage.setItem('aarka-theme', next);
        localStorage.setItem('aarkaa-theme', next);
      } catch {}
      applyThemeToDOM(next);
      return next;
    });
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    return {
      theme: 'dark' as Theme,
      toggleTheme: () => {},
      setTheme: () => {},
    };
  }
  return context;
}
