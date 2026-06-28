import React, { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'light';

interface ThemeContextType {
  theme: Theme;
  // keep signature for compatibility; toggle is a no-op in light-only mode
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | null>(null);

export const useTheme = (): ThemeContextType => {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
};

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme] = useState<Theme>(() => 'light');

  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove('dark');
    localStorage.setItem('theme', 'light');
  }, []);

  const toggleTheme = () => {
    /* no-op: light-only */
  };

  return <ThemeContext.Provider value={{ theme, toggleTheme }}>{children}</ThemeContext.Provider>;
};
