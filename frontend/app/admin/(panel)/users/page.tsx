"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { formatAuthMethod, formatRoles } from "@/components/admin/adminLabels";
import { AdminShell } from "@/components/admin/AdminShell";
import { EmptyState } from "@/components/admin/EmptyState";
import { InlineAlert } from "@/components/admin/InlineAlert";
import { LoadingState } from "@/components/admin/LoadingState";
import { DataTable } from "@/components/admin/PlaceholderPage";
import { VerificationBadge } from "@/components/admin/VerificationBadge";
import styles from "@/components/admin/admin.module.css";
import {
  AdminUserSummary,
  ApiError,
  VerificationStatus,
  fetchAdminUsers,
} from "@/lib/api";
import { useAdminAuth } from "@/lib/useAdminAuth";

const PAGE_SIZE = 25;

export default function AdminUsersPage() {
  const router = useRouter();
  const { token } = useAdminAuth();
  const [users, setUsers] = useState<AdminUserSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [query, setQuery] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [statusFilter, setStatusFilter] = useState<VerificationStatus | "">("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;

    setLoading(true);
    fetchAdminUsers(token, {
      q: query || undefined,
      verification_status: statusFilter || undefined,
      limit: PAGE_SIZE,
      offset,
    })
      .then((response) => {
        setUsers(response.items);
        setTotal(response.total);
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Unable to load users.");
        }
      })
      .finally(() => {
        setLoading(false);
      });
  }, [token, query, statusFilter, offset]);

  function handleSearch(event: FormEvent) {
    event.preventDefault();
    setOffset(0);
    setQuery(searchInput.trim());
  }

  return (
    <AdminShell title="Users" description="Search and manage registered accounts">
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}

      <form className={styles.toolbar} onSubmit={handleSearch}>
        <input
          type="search"
          placeholder="Search by email"
          value={searchInput}
          onChange={(event) => setSearchInput(event.target.value)}
        />
        <select
          value={statusFilter}
          onChange={(event) => {
            setOffset(0);
            setStatusFilter(event.target.value as VerificationStatus | "");
          }}
          aria-label="Filter by verification status"
        >
          <option value="">All statuses</option>
          <option value="unverified">Unverified</option>
          <option value="pending">Pending</option>
          <option value="verified">Verified</option>
          <option value="rejected">Rejected</option>
        </select>
        <button type="submit" className={styles.button}>
          Search
        </button>
      </form>

      {loading ? (
        <LoadingState label="Loading users" />
      ) : users.length === 0 ? (
        <EmptyState
          title="No users found"
          description={
            query || statusFilter
              ? "Try adjusting your search or filters."
              : "No registered users yet."
          }
          action={
            query || statusFilter
              ? undefined
              : { label: "Open verification queue", href: "/admin/verification" }
          }
        />
      ) : (
        <>
          <DataTable
            headers={["Email", "Roles", "Verification", "Sign-in", "Joined"]}
          >
            {users.map((user) => (
              <tr
                key={user.id}
                className={styles.tableRowLink}
                onClick={() => router.push(`/admin/users/${user.id}`)}
              >
                <td>
                  <Link href={`/admin/users/${user.id}`}>{user.email}</Link>
                  {user.is_admin ? " (admin)" : ""}
                </td>
                <td>{formatRoles(user)}</td>
                <td>
                  <VerificationBadge status={user.verification_status} />
                </td>
                <td>{formatAuthMethod(user.oauth_providers)}</td>
                <td>{new Date(user.created_at).toLocaleDateString()}</td>
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
