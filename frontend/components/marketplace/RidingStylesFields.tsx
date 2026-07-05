"use client";

import styles from "@/components/marketplace/marketplace.module.css";
import { RIDING_STYLE_OPTIONS, ridingStyleLabel } from "@/components/marketplace/marketplaceLabels";
import type { RidingStyle } from "@/lib/api";

interface RidingStylesFieldsProps {
  speciesName: string;
  defaultStyles?: RidingStyle[];
}

export function RidingStylesFields({
  speciesName,
  defaultStyles = [],
}: RidingStylesFieldsProps) {
  if (speciesName !== "horse") {
    return null;
  }

  return (
    <fieldset className={styles.ridingStylesFieldset}>
      <legend>Riding styles</legend>
      <p className={styles.cardMeta}>Select at least one style riders can expect for this horse.</p>
      <div className={styles.ridingStylesOptions}>
        {RIDING_STYLE_OPTIONS.map((style) => (
          <label key={style} className={styles.ridingStyleOption}>
            <input
              type="checkbox"
              name="riding_styles"
              value={style}
              defaultChecked={defaultStyles.includes(style)}
            />
            {ridingStyleLabel(style)}
          </label>
        ))}
      </div>
    </fieldset>
  );
}

export function parseRidingStylesFromForm(
  form: FormData,
  speciesName: string,
): RidingStyle[] {
  if (speciesName !== "horse") {
    return [];
  }
  return form.getAll("riding_styles").map(String) as RidingStyle[];
}

export function validateHorseRidingStyles(styles: RidingStyle[]): string | null {
  if (styles.length === 0) {
    return "Select at least one riding style (Western, English, or Therapy).";
  }
  return null;
}
