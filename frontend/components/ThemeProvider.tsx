"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  applyThemeToDocument,
  readStoredPreference,
  resolveTheme,
  THEME_STORAGE_KEY,
  type ResolvedTheme,
  type ThemePreference,
} from "@/lib/theme";

type ThemeContextValue = {
  preference: ThemePreference;
  resolved: ResolvedTheme;
  setPreference: (preference: ThemePreference) => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

function getInitialPreference(): ThemePreference {
  if (typeof window === "undefined") {
    return "system";
  }
  return readStoredPreference();
}

function getInitialResolved(): ResolvedTheme {
  if (typeof window === "undefined") {
    return "light";
  }
  return resolveTheme(readStoredPreference());
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [preference, setPreferenceState] =
    useState<ThemePreference>(getInitialPreference);
  const [resolved, setResolved] = useState<ResolvedTheme>(getInitialResolved);

  const setPreference = useCallback((next: ThemePreference) => {
    setPreferenceState(next);
    window.localStorage.setItem(THEME_STORAGE_KEY, next);
    const nextResolved = resolveTheme(next);
    setResolved(nextResolved);
    applyThemeToDocument(nextResolved);
  }, []);

  useEffect(() => {
    applyThemeToDocument(resolveTheme(preference));
  }, [preference]);

  useEffect(() => {
    if (preference !== "system") {
      return;
    }

    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => {
      const nextResolved = resolveTheme("system");
      setResolved(nextResolved);
      applyThemeToDocument(nextResolved);
    };

    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, [preference]);

  const value = useMemo(
    () => ({ preference, resolved, setPreference }),
    [preference, resolved, setPreference],
  );

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return context;
}
