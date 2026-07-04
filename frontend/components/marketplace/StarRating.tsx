import styles from "./marketplace.module.css";

interface StarRatingProps {
  value: number;
  max?: number;
  size?: "sm" | "md";
  showValue?: boolean;
}

export function StarRating({
  value,
  max = 5,
  size = "sm",
  showValue = false,
}: StarRatingProps) {
  const clamped = Math.max(0, Math.min(max, value));
  const fullStars = Math.floor(clamped);
  const hasHalf = clamped - fullStars >= 0.5;

  return (
    <span
      className={[styles.starRating, size === "md" ? styles.starRatingMd : ""]
        .filter(Boolean)
        .join(" ")}
      aria-label={`${clamped.toFixed(1)} out of ${max} stars`}
    >
      {Array.from({ length: max }, (_, index) => {
        const filled = index < fullStars || (index === fullStars && hasHalf);
        return (
          <span
            key={index}
            className={filled ? styles.starFilled : styles.starEmpty}
            aria-hidden="true"
          >
            ★
          </span>
        );
      })}
      {showValue ? <span className={styles.starValue}>{clamped.toFixed(1)}</span> : null}
    </span>
  );
}
