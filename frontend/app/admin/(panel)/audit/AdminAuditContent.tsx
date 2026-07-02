"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { auditActionLabel } from "@/components/admin/adminLabels";
import { AdminShell } from "@/components/admin/AdminShell";
import { EmptyState } from "@/components/admin/EmptyState";
import { InlineAlert } from "@/components/admin/InlineAlert";
import { LoadingState } from "@/components/admin/LoadingState";
import { DataTable } from "@/components/admin/PlaceholderPage";
import styles from "@/components/admin/admin.module.css";
import { AdminAuditLogEntry, ApiError, fetchAdminAudit } from "@/lib/api";
import { useAdminAuth } from "@/lib/useAdminAuth";

const PAGE_SIZE = 25;

function metadataSummary(metadata: Record<string, unknown>): string {
  const parts: string[] = [];
  if (
    typeof metadata.previous_status === "string" &&
    typeof metadata.new_status === "string"
  ) {
    parts.push(`${metadata.previous_status} → ${metadata.new_status}`);
  }
  if (typeof metadata.note === "string" && metadata.note) {
    parts.push(`Note: ${metadata.note}`);
  }
  if (typeof metadata.listing_id === "string") {
    parts.push(`Listing ${metadata.listing_id.slice(0, 8)}…`);
  }
  return parts.length > 0 ? parts.join(" · ") : "—";
}

export function AdminAuditContent() {
  const searchParams = useSearchParams();
  const targetUserId = searchParams.get("target_user_id");
  const { token } = useAdminAuth();
  const [entries, setEntries] = useState<AdminAuditLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    fetchAdminAudit(token, {
      target_user_id: targetUserId ?? undefined,
      limit: PAGE_SIZE,
      offset,
    })
      .then((response) => {
        setEntries(response.items);
        setTotal(response.total);
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Unable to load audit log.");
        }
      })
      .finally(() => setLoading(false));
  }, [token, targetUserId, offset]);

  return (
    <AdminShell
      title="Audit log"
      description={
        targetUserId
          ? "Admin actions for selected user"
          : "Read-only history of admin moderation actions"
      }
    >
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}

      {loading ? (
        <LoadingState label="Loading audit log" />
      ) : entries.length === 0 ? (
        <EmptyState
          title="No audit entries"
          description="Admin actions will appear here as moderators approve users or manage listings."
          action={{ label: "Open verification queue", href: "/admin/verification" }}
        />
      ) : (
        <>
          <DataTable
            headers={["Time", "Action", "Actor", "Target", "Details"]}
          >
            {entries.map((entry) => (
              <tr key={entry.id}>
                <td>{new Date(entry.created_at).toLocaleString()}</td>
                <td>{auditActionLabel(entry.action)}</td>
                <td>{entry.actor_email}</td>
                <td>
                  {entry.target_user_email && entry.target_user_id ? (
                    <Link href={`/admin/users/${entry.target_user_id}`}>
                      {entry.target_user_email}
                    </Link>
                  ) : (
                    "—"
                  )}
                </td>
                <td>{metadataSummary(entry.metadata)}</td>
              </tr>
            ))}
          </DataTable>

          <div className={styles.pagination}>
            <button
              type="button"
              className={`${styles.button} ${styles.buttonSecondary}`}
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            >
              Previous
            </button>
            <span>
              {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total}
            </span>
            <button
              type="button"
              className={`${styles.button} ${styles.buttonSecondary}`}
              disabled={offset + PAGE_SIZE >= total}
              onClick={() => setOffset(offset + PAGE_SIZE)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </AdminShell>
  );
}
