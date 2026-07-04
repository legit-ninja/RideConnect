"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { InlineAlert } from "@/components/marketplace/InlineAlert";
import styles from "@/components/marketplace/marketplace.module.css";
import {
  ApiError,
  User,
  confirmFriendInvite,
  fetchCurrentUser,
  fetchOwnerFriendInvites,
  redeemInviteToken,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

export function InviteRedeemPanel({ token }: { token: string }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null | undefined>(undefined);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const authToken = getToken();
    if (!authToken) {
      setUser(null);
      return;
    }
    fetchCurrentUser(authToken)
      .then(setUser)
      .catch(() => setUser(null));
  }, []);

  async function handleRedeem() {
    const authToken = getToken();
    if (!authToken) {
      router.push(`/login?src=invite&ref=${token}&next=/i/${token}`);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const result = await redeemInviteToken(authToken, token);
      setMessage(`Invite redeemed (${result.status}). The owner will confirm your connection.`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to redeem invite.");
    } finally {
      setBusy(false);
    }
  }

  if (user === undefined) return null;
  if (user === null) return null;

  if (user.verification_status !== "verified") {
    return (
      <InlineAlert variant="warning">
        Complete identity verification before redeeming this invite.
      </InlineAlert>
    );
  }

  return (
    <div className={styles.publicCta}>
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}
      {message ? <InlineAlert variant="success">{message}</InlineAlert> : null}
      <button type="button" className={styles.button} disabled={busy} onClick={handleRedeem}>
        {busy ? "Redeeming…" : "Redeem invite"}
      </button>
    </div>
  );
}

export function OwnerInviteConfirmQueue() {
  const [pending, setPending] = useState<
    { id: string; invitee_email: string; status: string }[]
  >([]);
  const [error, setError] = useState<string | null>(null);

  function load() {
    const token = getToken();
    if (!token) return;
    fetchOwnerFriendInvites(token)
      .then((response) =>
        setPending(
          response.items.filter((item) =>
            ["pending_owner_confirm", "pending_guardian"].includes(item.status),
          ),
        ),
      )
      .catch(() => setError("Unable to load pending invites."));
  }

  useEffect(() => {
    load();
  }, []);

  async function handleConfirm(inviteId: string, action: "confirm" | "decline") {
    const token = getToken();
    if (!token) return;
    setError(null);
    try {
      await confirmFriendInvite(token, inviteId, action);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Action failed.");
    }
  }

  if (pending.length === 0) return null;

  return (
    <div className={styles.shareBox}>
      <h2>Pending redemptions</h2>
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}
      <ul>
        {pending.map((invite) => (
          <li key={invite.id} style={{ marginBottom: "0.75rem" }}>
            {invite.invitee_email} — {invite.status.replace(/_/g, " ")}
            <div className={styles.shareRow}>
              <button
                type="button"
                className={styles.button}
                onClick={() => handleConfirm(invite.id, "confirm")}
              >
                Confirm
              </button>
              <button
                type="button"
                className={styles.buttonSecondary}
                onClick={() => handleConfirm(invite.id, "decline")}
              >
                Decline
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
