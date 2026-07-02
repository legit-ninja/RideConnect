import styles from "./admin.module.css";

interface QueueBadgeProps {
  count: number;
}

export function QueueBadge({ count }: QueueBadgeProps) {
  if (count <= 0) {
    return null;
  }

  return (
    <span className={styles.queueBadge} aria-label={`${count} items`}>
      {count > 99 ? "99+" : count}
    </span>
  );
}
