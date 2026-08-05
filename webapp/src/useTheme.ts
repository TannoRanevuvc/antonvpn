import { useState, useEffect, useCallback } from "react";
import type { Theme } from "./types";

const STORAGE_KEY = "antonvpn-theme";
const META_NAME = "theme-color";

function getSystemTheme(): Theme {
  if (typeof window === "undefined") return "dark";
  if (window.matchMedia("(prefers-color-scheme: dark)").matches) return "dark";
  return "light";
}

function getTgTheme(): Theme | null {
  try {
    const tg = (window as any).Telegram?.WebApp;
    if (!tg) return null;
    const cs = tg.colorScheme;
    if (cs === "light" || cs === "dark") return cs;
  } catch {
    /* ignore */
  }
  return null;
}

function applyTheme(theme: Theme) {
  document.documentElement.setAttribute("data-theme", theme);
  const themeColorMeta = document.querySelector(`meta[name="${META_NAME}"]`);
  const color = theme === "dark" ? "#0b0c0f" : "#f5f5f0";
  if (themeColorMeta) {
    themeColorMeta.setAttribute("content", color);
  }
  try {
    const tg = (window as any).Telegram?.WebApp;
    if (tg?.setHeaderColor) tg.setHeaderColor(color);
    if (tg?.setBackgroundColor) tg.setBackgroundColor(color);
  } catch {
    /* ignore */
  }
}

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>(() => {
    // apply theme immediately before first render to avoid flash
    const saved = localStorage.getItem(STORAGE_KEY) as Theme | null;
    const initial = saved ?? getTgTheme() ?? getSystemTheme();
    applyTheme(initial);
    return initial;
  });

  const setTheme = useCallback((next: Theme) => {
    setThemeState(next);
    applyTheme(next);
    localStorage.setItem(STORAGE_KEY, next);
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme(theme === "dark" ? "light" : "dark");
  }, [theme, setTheme]);

  // Follow system changes if no manual preference
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = (e: MediaQueryListEvent) => setTheme(e.matches ? "dark" : "light");
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, [setTheme]);

  return { theme, toggleTheme };
}
