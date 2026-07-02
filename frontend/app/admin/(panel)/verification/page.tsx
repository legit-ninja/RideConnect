"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { formatAuthMethod, formatRoles } from "@/components/admin/adminLabels";
import { AdminShell } from "@/components/admin/AdminShell";
import { EmptyState } from "@/components/admin/EmptyState";
import { InlineAlert } from "@/components/admin/InlineAlert";
import { LoadingState } from "@/components/admin/LoadingState";
import { DataTable } from "@/components/admin/PlaceholderPage";
import { VerificationBadge } from "@/components/admin/VerificationBadge";
import styles from "@/components/admin/admin.module.css";
import { AdminUserSummary, ApiError, fetchAdminUsers } from "@/lib/api";
import { useAdminAuth } from "@/lib/useAdminAuth";

export default function AdminVerificationPage() {
  const router = useRouter();
  const { token } = useAdminAuth();
  const [users, setUsers] = useState<AdminUserSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    Promise.all([
      fetchAdminUsers(token, {
        verification_status: "unverified",
        limit: 50,
        offset: 0,
      }),
      fetchAdminUsers(token, {
        verification_status: "pending",
        limit: 50,
        offset: 0,
      }),
    ])
      .then(([unverified, pending]) => {
        const combined = [...unverified.items, ...pending.items];
        combined.sort(
          (a, b) =>
            new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
        );
        setUsers(combined);
      })
      .catch(() => {
        setError("Unable to load verification queue.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [token]);

  return (
    <AdminShell
      title="Verification queue"
      description="Users awaiting manual KYC review (unverified and pending)"
    >
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}

      {loading ? (
        <LoadingState label="Loading verification queue" />
      ) : users.length === 0 ? (
        <EmptyState
          title="No users awaiting review"
          description="The verification queue is empty. New signups will appear here."
          action={{ label: "Browse all users", href: "/admin/users" }}
        />
      ) : (
        <DataTable
          headers={[
            "Email",
            "Roles",
            "Status",
            "Sign-in",
            "Minor",
            "Joined",
            "Actions",
          ]}
        >
          {users.map((user) => (
            <tr key={user.id}>
              <td>
                <Link href={`/admin/users/${user.id}`}>{user.email}</Link>
              </td>
              <td>{formatRoles(user)}</td>
              <td>
                <VerificationBadge status={user.verification_status} />
              </td>
              <td>{formatAuthMethod(user.oauth_providers)}</td>
              <td>{user.is_minor ? "Yes" : "—"}</td>
              <td>{new Date(user.created_at).toLocaleDateString()}</td>
              <td>
                <button
                  type="button"
                  className={styles.button}
                  onClick={() =>
                    router.push(`/admin/users/${user.id}?review=1`)
                  }
                >
                  Review
                </button>
              </td>
            </tr>
          ))}
        </DataTable>
      )}
    </AdminShell>
  );
}
