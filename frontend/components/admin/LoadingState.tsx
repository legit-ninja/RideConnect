import styles from "./admin.module.css";

interface LoadingStateProps {
  variant?: "stats" | "table";
  rows?: number;
  label?: string;
}

export function LoadingState({
  variant = "table",
  rows = 5,
  label = "Loading…",
}: LoadingStateProps) {
  if (variant === "stats") {
    return (
      <div role="status" aria-label={label}>
        <div className={styles.skeletonGrid}>
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className={styles.skeletonCard}>
              <div className={`${styles.skeletonLine} ${styles.skeletonLineShort}`} />
              <div className={`${styles.skeletonLine} ${styles.skeletonLineTall}`} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div role="status" aria-label={label}>
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className={styles.skeletonTableRow}>
          <div className={styles.skeletonLine} />
          <div className={styles.skeletonLine} />
          <div className={styles.skeletonLine} />
          <div className={styles.skeletonLine} />
        </div>
      ))}
    </div>
  );
}
