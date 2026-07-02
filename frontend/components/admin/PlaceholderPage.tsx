import Link from "next/link";
import { ReactNode } from "react";

import styles from "./admin.module.css";

interface PlaceholderPageProps {
  title: string;
  description: string;
  backHref?: string;
  backLabel?: string;
}

export function PlaceholderPage({
  title,
  description,
  backHref = "/admin/users",
  backLabel = "Back to users",
}: PlaceholderPageProps) {
  return (
    <div className={styles.placeholder}>
      <h2>{title}</h2>
      <p>{description}</p>
      <Link href={backHref} className={styles.button}>
        {backLabel}
      </Link>
    </div>
  );
}

interface DataTableProps {
  headers: string[];
  children: ReactNode;
}

export function DataTable({ headers, children }: DataTableProps) {
  return (
    <div className={styles.tableWrap}>
      <table className={styles.table}>
        <thead>
          <tr>
            {headers.map((header) => (
              <th key={header}>{header}</th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}
