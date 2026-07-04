"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { BlockedAction } from "@/components/marketplace/VerificationBanner";
import { OwnerInviteConfirmQueue } from "@/components/marketplace/InviteActions";
import { EmptyState } from "@/components/marketplace/EmptyState";
import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { LoadingState } from "@/components/marketplace/LoadingState";
import { PageHeader } from "@/components/marketplace/PageHeader";
import { friendStatusLabel } from "@/components/marketplace/marketplaceLabels";
import styles from "@/components/marketplace/marketplace.module.css";
import {
  ApiError,
  FriendInvite,
  InviteToken,
  User,
  cancelFriendInvite,
  createFriendInvite,
  createInviteToken,
  fetchCurrentUser,
  fetchInviteTokens,
  fetchOwnerFriendInvites,
  revokeInviteToken,
} from "@/lib/api";
import { getToken } from "@/lib/auth";
import { useRouter } from "next/navigation";

export default function OwnerFriendsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [invites, setInvites] = useState<FriendInvite[] | null>(null);
  const [tokens, setTokens] = useState<InviteToken[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);

  function loadData(token: string) {
    Promise.all([fetchOwnerFriendInvites(token), fetchInviteTokens(token)])
      .then(([inviteResponse, tokenResponse]) => {
        setInvites(inviteResponse.items);
        setTokens(tokenResponse.items);
      })
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
        loadData(token);
      })
      .catch(() => setError("Unable to load profile."));
  }, [router]);

  async function handleEmailSubmit(event: FormEvent<HTMLFormElement>) {
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
      loadData(token);
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Unable to send invite.");
    } finally {
      setBusy(false);
    }
  }

  async function handleCreateToken() {
    const token = getToken();
    if (!token) return;
    setBusy(true);
    setError(null);
    try {
      const created = await createInviteToken(token, {});
      setSuccess("Share link created.");
      setCopied(created.share_url);
      loadData(token);
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Unable to create link.");
    } finally {
      setBusy(false);
    }
  }

  async function handleRevokeToken(tokenId: string) {
    const token = getToken();
    if (!token) return;
    try {
      await revokeInviteToken(token, tokenId);
      loadData(token);
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Unable to revoke token.");
    }
  }

  async function handleCancel(inviteId: string) {
    const token = getToken();
    if (!token) return;
    setError(null);
    try {
      await cancelFriendInvite(token, inviteId);
      loadData(token);
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Unable to cancel invite.");
    }
  }

  function copyLink(url: string) {
    void navigator.clipboard.writeText(url);
    setCopied(url);
  }

  if (!user || invites === null || tokens === null) {
    return (
      <div className={styles.listingsPage}>
        <LoadingState variant="table" count={4} label="Loading friends" />
      </div>
    );
  }

  const activeTokens = tokens.filter((item) => !item.revoked_at);

  return (
    <div className={styles.listingsPage}>
      <PageHeader
        title="Verified friends"
        description="Invite riders by email or shareable link to unlock free-ride eligibility."
      />
      <BlockedAction user={user} action="send friend invites" />
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}
      {success ? <InlineAlert variant="success">{success}</InlineAlert> : null}
      {copied ? (
        <InlineAlert variant="success">Copied: {copied}</InlineAlert>
      ) : null}

      {user.verification_status === "verified" ? (
        <>
          <OwnerInviteConfirmQueue />

          <div className={styles.shareBox}>
            <h2>Shareable invite links</h2>
            <p className={styles.cardMeta}>
              Links can be forwarded — you confirm each redemption before the connection becomes
              active.
            </p>
            <button
              type="button"
              className={styles.button}
              disabled={busy}
              onClick={handleCreateToken}
            >
              Generate new link
            </button>
            {activeTokens.length > 0 ? (
              <ul>
                {activeTokens.map((item) => (
                  <li key={item.id} style={{ marginTop: "0.75rem" }}>
                    <code>{item.share_url}</code>
                    <div className={styles.shareRow}>
                      <button
                        type="button"
                        className={styles.buttonSecondary}
                        onClick={() => copyLink(item.share_url)}
                      >
                        Copy
                      </button>
                      <button
                        type="button"
                        className={styles.buttonSecondary}
                        onClick={() => handleRevokeToken(item.id)}
                      >
                        Revoke
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>

          <form onSubmit={handleEmailSubmit} className={styles.formPage}>
            <label>
              Rider email
              <input name="invitee_email" type="email" required placeholder="rider@example.com" />
            </label>
            <button className={styles.button} type="submit" disabled={busy}>
              {busy ? "Sending…" : "Send email invite"}
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
                        {invite.status === "pending_owner_confirm" ? (
                          <button
                            type="button"
                            className={styles.buttonSecondary}
                            onClick={() => handleCancel(invite.id)}
                          >
                            Revoke
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
