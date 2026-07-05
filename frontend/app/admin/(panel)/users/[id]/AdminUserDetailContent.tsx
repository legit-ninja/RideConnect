"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import {
  auditActionLabel,
  formatAuthMethod,
  formatTrainerSelfReport,
} from "@/components/admin/adminLabels";
import { AdminShell } from "@/components/admin/AdminShell";
import { ConfirmDialog } from "@/components/admin/ConfirmDialog";
import { InlineAlert } from "@/components/admin/InlineAlert";
import { LoadingState } from "@/components/admin/LoadingState";
import { VerificationBadge } from "@/components/admin/VerificationBadge";
import styles from "@/components/admin/admin.module.css";
import {
  AdminAuditLogEntry,
  AdminUserDetail,
  ApiError,
  VerificationStatus,
  fetchAdminAudit,
  fetchAdminUser,
  updateUserRoles,
  updateTrainerVerification,
  updateUserVerification,
} from "@/lib/api";
import { useAdminAuth } from "@/lib/useAdminAuth";

type PendingAction = {
  status: VerificationStatus;
  destructive: boolean;
};

export function AdminUserDetailContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  const userId = params.id as string;
  const reviewMode = searchParams.get("review") === "1";
  const router = useRouter();
  const { token } = useAdminAuth();
  const [user, setUser] = useState<AdminUserDetail | null>(null);
  const [recentAudit, setRecentAudit] = useState<AdminAuditLogEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isRider, setIsRider] = useState(false);
  const [isOwner, setIsOwner] = useState(false);
  const [trainerVerified, setTrainerVerified] = useState(false);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [pendingAction, setPendingAction] = useState<PendingAction | null>(null);

  function loadUser() {
    if (!token) return;
    fetchAdminUser(token, userId)
      .then((detail) => {
        setUser(detail);
        setIsRider(detail.is_rider);
        setIsOwner(detail.is_owner);
        setTrainerVerified(detail.trainer_verified);
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Unable to load user.");
        }
      });

    fetchAdminAudit(token, { target_user_id: userId, limit: 5 })
      .then((response) => setRecentAudit(response.items))
      .catch(() => {
        setRecentAudit([]);
      });
  }

  useEffect(() => {
    loadUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, userId]);

  async function submitVerification(status: VerificationStatus) {
    if (!token || !user) return;
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const updated = await updateUserVerification(token, user.id, {
        verification_status: status,
        note: note.trim() || undefined,
      });
      setUser(updated);
      setNote("");
      setSuccess(
        status === "verified"
          ? "User approved. Action logged in audit trail."
          : status === "rejected"
            ? "User rejected. They cannot host or request rides until re-verified."
            : "Verification marked pending. Action logged.",
      );
      loadUser();
      if (reviewMode && status !== "pending") {
        router.push("/admin/verification");
      }
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Update failed.");
    } finally {
      setBusy(false);
      setPendingAction(null);
    }
  }

  function requestVerification(status: VerificationStatus) {
    if (status === "rejected") {
      setPendingAction({ status, destructive: true });
      return;
    }
    void submitVerification(status);
  }

  async function handleRolesSave() {
    if (!token || !user) return;
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const updated = await updateUserRoles(token, user.id, {
        is_rider: isRider,
        is_owner: isOwner,
      });
      setUser(updated);
      setSuccess("Roles updated. Action logged.");
      loadUser();
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Update failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleTrainerVerifiedSave() {
    if (!token || !user) return;
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const updated = await updateTrainerVerification(token, user.id, {
        trainer_verified: trainerVerified,
        note: note.trim() || undefined,
      });
      setUser(updated);
      setSuccess("Trainer verification updated.");
      loadUser();
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Update failed.");
    } finally {
      setBusy(false);
    }
  }

  if (!user && !error) {
    return (
      <AdminShell title="User detail">
        <LoadingState label="Loading user" />
      </AdminShell>
    );
  }

  if (error && !user) {
    return (
      <AdminShell title="User detail">
        <InlineAlert variant="error">{error}</InlineAlert>
        <Link href="/admin/users">Back to users</Link>
      </AdminShell>
    );
  }

  if (!user) {
    return null;
  }

  const guardianWarning =
    user.is_minor &&
    (!user.guardian || user.guardian.verification_status !== "verified");

  return (
    <AdminShell
      title={user.email}
      description={
        reviewMode
          ? "Review identity before approving ride activity"
          : "User profile and admin actions"
      }
      actions={
        <Link
          href="/admin/users"
          className={`${styles.button} ${styles.buttonSecondary}`}
        >
          Back to users
        </Link>
      }
    >
      {reviewMode ? (
        <div className={styles.reviewBanner}>
          <InlineAlert variant="info">
            Review mode — verify identity manually. OAuth sign-in does not verify
            identity for rides.
          </InlineAlert>
        </div>
      ) : null}

      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}
      {success ? <InlineAlert variant="success">{success}</InlineAlert> : null}

      {guardianWarning ? (
        <InlineAlert variant="warning">
          Minor account — a verified guardian is required before any ride activity.
          {user.guardian
            ? ` Guardian ${user.guardian.email} is ${user.guardian.verification_status}.`
            : " No guardian linked."}
        </InlineAlert>
      ) : null}

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Identity and verification</h2>
        <div className={styles.card}>
          <div className={styles.detailGrid}>
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Verification</span>
              <VerificationBadge status={user.verification_status} />
            </div>
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Sign-in</span>
              <span>
                {user.oauth_accounts.length > 0
                  ? user.oauth_accounts
                      .map(
                        (account) =>
                          `Signed in with ${account.provider}${account.provider_email ? ` (${account.provider_email})` : ""}`,
                      )
                      .join("; ")
                  : formatAuthMethod([])}
              </span>
            </div>
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Minor</span>
              <span>{user.is_minor ? "Yes" : "No"}</span>
            </div>
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Phone</span>
              <span>{user.phone ?? "—"}</span>
            </div>
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Joined</span>
              <span>{new Date(user.created_at).toLocaleString()}</span>
            </div>
          </div>

          <label htmlFor="admin-note" className={styles.detailLabel}>
            Admin note (optional)
          </label>
          <textarea
            id="admin-note"
            className={styles.textarea}
            value={note}
            onChange={(event) => setNote(event.target.value)}
            placeholder="Reason for approval or rejection (stored in audit log)"
            maxLength={500}
          />

          <div className={styles.buttonGroup}>
            <button
              type="button"
              className={styles.button}
              disabled={busy}
              onClick={() => requestVerification("verified")}
            >
              Approve
            </button>
            <button
              type="button"
              className={`${styles.button} ${styles.buttonSecondary}`}
              disabled={busy}
              onClick={() => requestVerification("pending")}
            >
              Mark pending
            </button>
            <button
              type="button"
              className={`${styles.button} ${styles.buttonDanger}`}
              disabled={busy}
              onClick={() => requestVerification("rejected")}
            >
              Reject
            </button>
          </div>
        </div>
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Roles</h2>
        <div className={styles.card}>
          <div className={styles.toolbar}>
            <label>
              <input
                type="checkbox"
                checked={isRider}
                onChange={(event) => setIsRider(event.target.checked)}
              />{" "}
              Rider
            </label>
            <label>
              <input
                type="checkbox"
                checked={isOwner}
                onChange={(event) => setIsOwner(event.target.checked)}
              />{" "}
              Owner
            </label>
            <button
              type="button"
              className={styles.button}
              disabled={busy}
              onClick={handleRolesSave}
            >
              Save roles
            </button>
          </div>
        </div>
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Trainer claims</h2>
        <div className={styles.card}>
          <p>{formatTrainerSelfReport(user)}</p>
          <div className={styles.toolbar}>
            <label>
              <input
                type="checkbox"
                checked={trainerVerified}
                onChange={(event) => setTrainerVerified(event.target.checked)}
              />{" "}
              Verified trainer badge (admin only)
            </label>
            <button
              type="button"
              className={styles.button}
              disabled={busy}
              onClick={handleTrainerVerifiedSave}
            >
              Save trainer verification
            </button>
          </div>
        </div>
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Marketplace activity</h2>
        <div className={styles.card}>
          <div className={styles.detailGrid}>
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Animals</span>
              <span>{user.animal_count}</span>
            </div>
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Listings</span>
              <span>
                {user.listing_count} total ({user.active_listing_count} active)
              </span>
            </div>
          </div>
          {user.listing_count > 0 ? (
            <Link
              href={`/admin/listings?owner_id=${user.id}`}
              className={styles.button}
            >
              View user listings
            </Link>
          ) : null}
        </div>
      </section>

      {recentAudit.length > 0 ? (
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Recent audit history</h2>
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Action</th>
                  <th>Actor</th>
                </tr>
              </thead>
              <tbody>
                {recentAudit.map((entry) => (
                  <tr key={entry.id}>
                    <td>{new Date(entry.created_at).toLocaleString()}</td>
                    <td>{auditActionLabel(entry.action)}</td>
                    <td>{entry.actor_email}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Link
            href={`/admin/audit?target_user_id=${user.id}`}
            className={styles.muted}
          >
            View full audit log →
          </Link>
        </section>
      ) : null}

      <ConfirmDialog
        open={pendingAction !== null}
        title="Reject verification?"
        description="This user cannot host or request rides until they are re-verified. This action is logged in the audit trail."
        confirmLabel="Reject user"
        destructive
        onConfirm={() => {
          if (pendingAction) {
            void submitVerification(pendingAction.status);
          }
        }}
        onCancel={() => setPendingAction(null)}
      />
    </AdminShell>
  );
}
