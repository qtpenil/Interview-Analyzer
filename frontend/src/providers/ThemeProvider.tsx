"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  cssVarMap,
  DEFAULT_THEME,
  themes,
  THEME_COOKIE_KEY,
  THEME_STORAGE_KEY,
  type ThemeName,
  type ThemeTokens,
} from "@/styles/theme";

type ThemeContextValue = {
  theme: ThemeName;
  tokens: ThemeTokens;
  toggleTheme: () => void;
  setTheme: (name: ThemeName) => void;
};

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

function applyTheme(name: ThemeName) {
  const root = document.documentElement;
  const tokens = themes[name];
  (Object.keys(cssVarMap) as (keyof ThemeTokens)[]).forEach((key) => {
    root.style.setProperty(cssVarMap[key], tokens[key]);
  });
  root.setAttribute("data-theme", name);
  root.classList.toggle("theme-light", name === "light");
  root.classList.toggle("theme-dark", name === "dark");
}

export function ThemeProvider({
  children,
  initialTheme = DEFAULT_THEME,
}: {
  children: ReactNode;
  initialTheme?: ThemeName;
}) {
  // Seed from the server-resolved theme so the first client render matches the
  // server-rendered HTML (prevents React hydration mismatches). The pre-hydration
  // script in layout.tsx has already applied the same theme to <html>.
  const [theme, setThemeState] = useState<ThemeName>(initialTheme);

  useEffect(() => {
    // Sync React state to the theme the pre-hydration script actually applied
    // to <html> (it may differ from initialTheme for legacy localStorage-only
    // users). We sync from the DOM here, not during render, to avoid a mismatch.
    const current = document.documentElement.getAttribute("data-theme");
    if (current === "dark" || current === "light") {
      setThemeState(current);
    }
    // Enable transitions only after first paint to avoid an initial flash.
    const id = window.setTimeout(() => {
      document.documentElement.classList.add("theme-transitions");
    }, 0);
    return () => window.clearTimeout(id);
  }, []);

  const setTheme = useCallback((name: ThemeName) => {
    applyTheme(name);
    setThemeState(name);
    try {
      localStorage.setItem(THEME_STORAGE_KEY, name);
    } catch {
      /* ignore storage errors (private mode, etc.) */
    }
    // Mirror the choice in a cookie so the server can render the same
    // theme during SSR — this prevents React hydration mismatches.
    try {
      document.cookie = `${THEME_COOKIE_KEY}=${name};path=/;max-age=31536000;samesite=lax`;
    } catch {
      /* ignore */
    }
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme(theme === "dark" ? "light" : "dark");
  }, [theme, setTheme]);

  const value = useMemo<ThemeContextValue>(
    () => ({ theme, tokens: themes[theme], toggleTheme, setTheme }),
    [theme, toggleTheme, setTheme]
  );

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
}

export function useThemeContext() {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error("useThemeContext must be used within a ThemeProvider");
  }
  return ctx;
}

// Inline script injected before hydration to set the theme without a flash.
// It reads the theme cookie (so it agrees with the server-rendered <html>),
// falling back to localStorage for users who set their theme before cookies
// were introduced. It writes both back so server and client stay in sync.
export const themeInitScript = `
(function () {
  try {
    var key = "${THEME_COOKIE_KEY}";
    var m = document.cookie.match(new RegExp("(?:^|; )" + key + "=([^;]*)"));
    var cookieTheme = m ? decodeURIComponent(m[1]) : null;
    var stored = localStorage.getItem("${THEME_STORAGE_KEY}");
    var theme = cookieTheme || stored || "${DEFAULT_THEME}";
    if (theme !== "dark" && theme !== "light") theme = "${DEFAULT_THEME}";
    if (theme !== cookieTheme) {
      document.cookie = key + "=" + theme + ";path=/;max-age=31536000;samesite=lax";
    }
    if (stored !== theme) {
      localStorage.setItem("${THEME_STORAGE_KEY}", theme);
    }
    var root = document.documentElement;
    var map = ${JSON.stringify(cssVarMap)};
    var themes = ${JSON.stringify(themes)};
    var tokens = themes[theme];
    Object.keys(map).forEach(function (k) {
      root.style.setProperty(map[k], tokens[k]);
    });
    root.setAttribute("data-theme", theme);
    root.classList.add(theme === "light" ? "theme-light" : "theme-dark");
  } catch (e) {}
})();
`;
