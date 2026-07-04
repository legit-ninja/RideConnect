"use client";

import { useEffect, useState } from "react";

import { AdminShell } from "@/components/admin/AdminShell";
import { EmptyState } from "@/components/admin/EmptyState";
import styles from "@/components/marketplace/marketplace.module.css";
import { AdminPlatformFlag, fetchAdminFlags } from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function AdminReportsPage() {
  const [flags, setFlags] = useState<AdminPlatformFlag[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    fetchAdminFlags(token)
      .then((response) => setFlags(response.items))
      .catch(() => setError("Unable to load platform flags."));
  }, []);

  return (
    <AdminShell
      title="Reports"
      description="Trust and safety pattern flags for manual review."
    >
      {error ? <p className={styles.error}>{error}</p> : null}
      {flags === null ? (
        <p>Loading flags…</p>
      ) : flags.length === 0 ? (
        <EmptyState
          title="No open flags"
          description="Automated pattern alerts (e.g. high invite redemption rate) will appear here."
          action={{ label: "Open verification queue", href: "/admin/verification" }}
        />
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Type</th>
                <th>User</th>
                <th>Created</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {flags.map((flag) => (
                <tr key={flag.id}>
                  <td>{flag.flag_type.replace(/_/g, " ")}</td>
                  <td>{flag.user_email}</td>
                  <td>{new Date(flag.created_at).toLocaleString()}</td>
                  <td>
                    <code>{JSON.stringify(flag.details ?? {})}</code>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AdminShell>
  );
}
