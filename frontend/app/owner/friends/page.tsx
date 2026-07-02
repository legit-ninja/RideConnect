"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { BlockedAction } from "@/components/marketplace/VerificationBanner";
import { EmptyState } from "@/components/marketplace/EmptyState";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { LoadingState } from "@/components/marketplace/LoadingState";
import { PageHeader } from "@/components/marketplace/PageHeader";
import { friendStatusLabel } from "@/components/marketplace/marketplaceLabels";
import styles from "@/components/marketplace/marketplace.module.css";
import {
  ApiError,
  FriendInvite,
  User,
  cancelFriendInvite,
  createFriendInvite,
  fetchCurrentUser,
  fetchOwnerFriendInvites,
} from "@/lib/api";
import { getToken } from "@/lib/auth";
import { useRouter } from "next/navigation";

export default function OwnerFriendsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [invites, setInvites] = useState<FriendInvite[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function loadInvites(token: string) {
    fetchOwnerFriendInvites(token)
      .then((response) => setInvites(response.items))
      .catch(() => setError("Unable to load friend invites."));
  }

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    fetchCurrentUser(token)
      .then((currentUser) => {
        setUser(currentUser);
        if (!currentUser.is_owner) {
          router.replace("/dashboard");
          return;
        }
        loadInvites(token);
      })
      .catch(() => setError("Unable to load profile."));
  }, [router]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getToken();
    if (!token) return;
    setBusy(true);
    setError(null);
    setSuccess(null);
    const form = event.currentTarget;
    const email = String(new FormData(form).get("invitee_email"));
    try {
      await createFriendInvite(token, { invitee_email: email });
      setSuccess(`Invite sent to ${email}.`);
      form.reset();
      loadInvites(token);
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Unable to send invite.");
    } finally {
      setBusy(false);
    }
  }

  async function handleCancel(inviteId: string) {
    const token = getToken();
    if (!token) return;
    setError(null);
    try {
      await cancelFriendInvite(token, inviteId);
      loadInvites(token);
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Unable to cancel invite.");
    }
  }

  if (!user || invites === null) {
    return (
      <div className={styles.listingsPage}>
        <LoadingState variant="table" count={4} label="Loading friends" />
      </div>
    );
  }

  return (
    <div className={styles.listingsPage}>
      <PageHeader
        title="Verified friends"
        description="Invite riders by email to unlock free-ride eligibility on friend-only listings."
      />
      <BlockedAction user={user} action="send friend invites" />
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}
      {success ? <InlineAlert variant="success">{success}</InlineAlert> : null}

      {user.verification_status === "verified" ? (
        <>
          <form onSubmit={handleSubmit} className={styles.formPage}>
            <label>
              Rider email
              <input name="invitee_email" type="email" required placeholder="rider@example.com" />
            </label>
            <button className={styles.button} type="submit" disabled={busy}>
              {busy ? "Sending…" : "Send invite"}
            </button>
          </form>

          {invites.length === 0 ? (
            <EmptyState
              title="No invites yet"
              description="Send an invite to a verified rider to unlock free rides between you."
            />
          ) : (
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Email</th>
                    <th>Status</th>
                    <th>Sent</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {invites.map((invite) => (
                    <tr key={invite.id}>
                      <td>{invite.invitee_email}</td>
                      <td>{friendStatusLabel(invite.status)}</td>
                      <td>{new Date(invite.invited_at).toLocaleDateString()}</td>
                      <td>
                        {invite.status === "pending" ? (
                          <button
                            type="button"
                            className={styles.buttonSecondary}
                            onClick={() => handleCancel(invite.id)}
                          >
                            Cancel
                          </button>
                        ) : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      ) : null}

      <p>
        <Link href="/dashboard">Back to dashboard</Link>
      </p>
    </div>
  );
}
