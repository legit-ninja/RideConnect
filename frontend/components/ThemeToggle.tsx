"use client";

import { THEME_LABELS, THEME_PREFERENCES } from "@/lib/theme";

import { useTheme } from "./ThemeProvider";
import styles from "./ThemeToggle.module.css";

export function ThemeToggle() {
  const { preference, setPreference } = useTheme();

  return (
    <fieldset className={styles.fieldset}>
      <legend className={styles.legend}>Theme</legend>
      <div className={styles.options} role="radiogroup" aria-label="Theme">
        {THEME_PREFERENCES.map((option) => (
          <label key={option} className={styles.option}>
            <input
              type="radio"
              name="theme"
              value={option}
              checked={preference === option}
              onChange={() => setPreference(option)}
            />
            <span>{THEME_LABELS[option]}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
