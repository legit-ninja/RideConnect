import styles from "./admin.module.css";

interface StatCardProps {
  label: string;
  value: number;
}

export function StatCard({ label, value }: StatCardProps) {
  return (
    <div className={styles.statCard}>
      <div className={styles.statCardLabel}>{label}</div>
      <div className={styles.statCardValue}>{value}</div>
    </div>
  );
}
