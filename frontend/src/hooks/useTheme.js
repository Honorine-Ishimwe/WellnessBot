/**
 * useTheme — custom hook for dark/light mode management.
 * Extracts theme logic from App.js into a reusable hook.
 */

import { useState, useEffect } from "react";

const THEME_KEY = "wellnessbot_theme";

export default function useTheme() {
  const [darkMode, setDarkMode] = useState(() => {
    const stored = localStorage.getItem(THEME_KEY);
    if (stored) return stored === "dark";
    return typeof window !== "undefined" && typeof window.matchMedia === "function"
      ? window.matchMedia("(prefers-color-scheme: dark)").matches
      : false;
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
    localStorage.setItem(THEME_KEY, darkMode ? "dark" : "light");
  }, [darkMode]);

  const toggleTheme = () => setDarkMode((d) => !d);

  return { darkMode, toggleTheme };
}
