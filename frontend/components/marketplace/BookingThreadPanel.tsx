"use client";

import { FormEvent, useEffect, useState } from "react";

import { InlineAlert } from "@/components/marketplace/InlineAlert";
import styles from "@/components/marketplace/marketplace.module.css";
import { ApiError, ThreadMessage, fetchThreadMessages, postThreadMessage } from "@/lib/api";
import { getToken } from "@/lib/auth";

interface BookingThreadPanelProps {
  threadId: string;
}

export function BookingThreadPanel({ threadId }: BookingThreadPanelProps) {
  const [messages, setMessages] = useState<ThreadMessage[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function loadMessages() {
    const token = getToken();
    if (!token) return;
    fetchThreadMessages(token, threadId)
      .then((response) => setMessages(response.items))
      .catch(() => setError("Unable to load messages."));
  }

  useEffect(() => {
    loadMessages();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [threadId]);

  async function handleReply(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getToken();
    if (!token) return;
    const body = String(new FormData(event.currentTarget).get("body") || "").trim();
    if (!body) return;
    setBusy(true);
    setError(null);
    try {
      await postThreadMessage(token, threadId, body);
      event.currentTarget.reset();
      loadMessages();
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Unable to send message.");
    } finally {
      setBusy(false);
    }
  }

  if (messages === null) {
    return <p className={styles.cardMeta}>Loading messages…</p>;
  }

  return (
    <div className={styles.shareBox}>
      <h3>Messages</h3>
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}
      {messages.length === 0 ? (
        <p className={styles.cardMeta}>No messages yet.</p>
      ) : (
        <ul className={styles.slotList}>
          {messages.map((message) => (
            <li key={message.id} className={styles.slotRow}>
              <p>{message.body}</p>
              <span className={styles.slotMeta}>
                {new Date(message.sent_at).toLocaleString()}
              </span>
            </li>
          ))}
        </ul>
      )}
      <form onSubmit={handleReply} className={styles.formPage}>
        <label>
          Reply
          <textarea name="body" rows={2} maxLength={2000} required />
        </label>
        <button type="submit" className={styles.buttonSecondary} disabled={busy}>
          {busy ? "Sending…" : "Send message"}
        </button>
      </form>
    </div>
  );
}
