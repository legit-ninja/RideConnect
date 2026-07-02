import styles from "./marketplace.module.css";

interface LoadingStateProps {
  variant?: "cards" | "table";
  count?: number;
  label?: string;
}

export function LoadingState({
  variant = "cards",
  count = 6,
  label = "Loading…",
}: LoadingStateProps) {
  if (variant === "table") {
    return (
      <div role="status" aria-label={label}>
        {Array.from({ length: count }).map((_, index) => (
          <div key={index} className={`${styles.skeletonLine} ${styles.skeletonTableLine}`} />
        ))}
      </div>
    );
  }

  return (
    <div className={styles.skeletonGrid} role="status" aria-label={label}>
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className={styles.skeletonCard}>
          <div className={`${styles.skeletonLine} ${styles.skeletonImage}`} />
          <div className={styles.skeletonLine} />
          <div className={styles.skeletonLine} />
        </div>
      ))}
    </div>
  );
}
