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
 * Read the stored theme, always returning 'light'.
 */
function getStoredTheme(): Theme {
  return 'light';
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>('light');

  // Apply light theme immediately on first client render
  useEffect(() => {
    applyThemeToDOM('light');
    try {
      localStorage.setItem('aarka-theme', 'light');
      localStorage.setItem('aarkaa-theme', 'light');
    } catch {}
  }, []);

  const setTheme = useCallback((t: Theme) => {
    setThemeState('light');
    applyThemeToDOM('light');
  }, []);

  const toggleTheme = useCallback(() => {
    setThemeState('light');
    applyThemeToDOM('light');
  }, []);

  return (
    <ThemeContext.Provider value={{ theme: 'light', toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    return {
      theme: 'light' as Theme,
      toggleTheme: () => {},
      setTheme: () => {},
    };
  }
  return context;
}
