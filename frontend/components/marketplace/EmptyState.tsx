import Link from "next/link";
import { ReactNode } from "react";

import styles from "./marketplace.module.css";

interface EmptyStateProps {
  title: string;
  description: string;
  action?: { label: string; href: string };
  children?: ReactNode;
}

export function EmptyState({ title, description, action, children }: EmptyStateProps) {
  return (
    <div className={styles.emptyState}>
      <div className={styles.emptyStateIcon} aria-hidden="true">
        ◎
      </div>
      <h2 className={styles.emptyStateTitle}>{title}</h2>
      <p className={styles.emptyStateDescription}>{description}</p>
      {action ? (
        <Link href={action.href} className={styles.button}>
          {action.label}
        </Link>
      ) : null}
      {children}
    </div>
  );
}
