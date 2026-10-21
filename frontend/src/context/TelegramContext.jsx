import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';

const TelegramContext = createContext(null);

export function TelegramProvider({ children }) {
  const [tg, setTg] = useState(null);
  const [user, setUser] = useState(null);
  const [initData, setInitData] = useState('');
  const [activeRole, setActiveRole] = useState('client'); // 'client' | 'admin'
  const [colorScheme, setColorScheme] = useState('light');
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => {
    const webApp = window.Telegram?.WebApp;
    // Check url query params for demo flag
    const urlParams = new URLSearchParams(window.location.search);
    const demoParam = urlParams.get('demo');
    if (demoParam === 'true') {
      setIsDemo(true);
    }

    if (webApp) {
      webApp.ready();
      try {
        webApp.expand();
      } catch (e) {
        console.warn('Could not expand WebApp viewport:', e);
      }

      setTg(webApp);
      setColorScheme(webApp.colorScheme || 'light');

      if (webApp.colorScheme === 'dark') {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }

      if (webApp.initData) {
        setInitData(webApp.initData);
      }

      if (webApp.initDataUnsafe?.user) {
        setUser(webApp.initDataUnsafe.user);
      }

      // Listen for theme changes
      const handleThemeChange = () => {
        setColorScheme(webApp.colorScheme || 'light');
        if (webApp.colorScheme === 'dark') {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
      };

      webApp.onEvent('themeChanged', handleThemeChange);
      return () => {
        webApp.offEvent('themeChanged', handleThemeChange);
      };
    }
  }, []);

  // Compute effective initData string (supports mock bypass when opening in standard browser)
  const getEffectiveInitData = useCallback(() => {
    if (initData) {
      return initData;
    }
    // Dev fallback if opened outside Telegram or testing
    return activeRole === 'admin' ? 'mock_admin' : 'mock_client';
  }, [initData, activeRole]);

  // Haptic Feedback helper
  const haptic = useCallback(
    (type = 'light') => {
      if (!tg?.HapticFeedback) return;
      try {
        if (type === 'light' || type === 'medium' || type === 'heavy') {
          tg.HapticFeedback.impactOccurred(type);
        } else if (type === 'success' || type === 'error' || type === 'warning') {
          tg.HapticFeedback.notificationOccurred(type);
        } else if (type === 'selection') {
          tg.HapticFeedback.selectionChanged();
        }
      } catch (err) {
        console.debug('Haptics not available:', err);
      }
    },
    [tg]
  );

  const openLink = useCallback(
    (url) => {
      haptic('light');
      if (tg?.openLink) {
        tg.openLink(url);
      } else {
        window.open(url, '_blank');
      }
    },
    [tg, haptic]
  );

  const value = {
    tg,
    user,
    initData: getEffectiveInitData(),
    rawInitData: initData,
    activeRole,
    setActiveRole,
    colorScheme,
    isDemo,
    haptic,
    openLink,
  };

  return <TelegramContext.Provider value={value}>{children}</TelegramContext.Provider>;
}

export function useTelegram() {
  const context = useContext(TelegramContext);
  if (!context) {
    throw new Error('useTelegram must be used within a TelegramProvider');
  }
  return context;
}
