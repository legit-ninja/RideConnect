export const THEME_STORAGE_KEY = "rideconnect-theme";

export type ThemePreference = "light" | "dark" | "system" | "high-contrast";

export type ResolvedTheme = "light" | "dark" | "high-contrast";

export const THEME_PREFERENCES: ThemePreference[] = [
  "light",
  "dark",
  "system",
  "high-contrast",
];

export function isThemePreference(value: string): value is ThemePreference {
  return THEME_PREFERENCES.includes(value as ThemePreference);
}

export function getSystemTheme(): "light" | "dark" {
  if (typeof window === "undefined") {
    return "light";
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export function resolveTheme(preference: ThemePreference): ResolvedTheme {
  if (preference === "high-contrast") {
    return "high-contrast";
  }
  if (preference === "system") {
    return getSystemTheme();
  }
  return preference;
}

export function readStoredPreference(): ThemePreference {
  if (typeof window === "undefined") {
    return "system";
  }
  const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
  if (stored && isThemePreference(stored)) {
    return stored;
  }
  return "system";
}

export function applyThemeToDocument(resolved: ResolvedTheme): void {
  if (typeof document === "undefined") {
    return;
  }
  document.documentElement.setAttribute("data-theme", resolved);
}

export const THEME_LABELS: Record<ThemePreference, string> = {
  light: "Light",
  dark: "Dark",
  system: "System",
  "high-contrast": "High contrast",
};

/** Inline script string for layout FOUC prevention — keep in sync with resolveTheme(). */
export const THEME_INIT_SCRIPT = `(function(){try{var k="rideconnect-theme";var p=localStorage.getItem(k);var valid=["light","dark","system","high-contrast"];if(!p||valid.indexOf(p)<0)p="system";var t=p;if(p==="system"){t=window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light";}else if(p==="high-contrast"){t="high-contrast";}document.documentElement.setAttribute("data-theme",t);}catch(e){}})();`;
