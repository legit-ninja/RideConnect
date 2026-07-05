"use client";

import { FormEvent, useEffect, useState } from "react";

import { InlineAlert } from "@/components/marketplace/InlineAlert";
import styles from "@/components/marketplace/marketplace.module.css";
import {
  ApiError,
  AvailabilitySlot,
  createOwnerListingSlot,
  deleteOwnerListingSlot,
  fetchOwnerListingSlots,
  updateOwnerListingSlot,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

function formatSlotRange(start: string, end: string): string {
  const startDate = new Date(start);
  const endDate = new Date(end);
  return `${startDate.toLocaleDateString()} · ${startDate.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })} – ${endDate.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}`;
}

function toIsoDateTime(date: string, time: string): string {
  return new Date(`${date}T${time}`).toISOString();
}

interface ListingSlotsSectionProps {
  listingId: string;
}

export function ListingSlotsSection({ listingId }: ListingSlotsSectionProps) {
  const [slots, setSlots] = useState<AvailabilitySlot[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function loadSlots() {
    const token = getToken();
    if (!token) return;
    fetchOwnerListingSlots(token, listingId)
      .then(setSlots)
      .catch(() => setError("Unable to load availability slots."));
  }

  useEffect(() => {
    loadSlots();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listingId]);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = getToken();
    if (!token) return;
    setBusy(true);
    setError(null);
    setSuccess(null);
    const form = new FormData(event.currentTarget);
    const date = String(form.get("slot_date"));
    const startTime = String(form.get("start_time"));
    const endTime = String(form.get("end_time"));
    try {
      await createOwnerListingSlot(token, listingId, {
        start_at: toIsoDateTime(date, startTime),
        end_at: toIsoDateTime(date, endTime),
      });
      setSuccess("Availability slot added.");
      event.currentTarget.reset();
      loadSlots();
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Could not create slot.");
    } finally {
      setBusy(false);
    }
  }

  async function blockSlot(slotId: string) {
    const token = getToken();
    if (!token) return;
    setBusy(true);
    setError(null);
    try {
      await updateOwnerListingSlot(token, listingId, slotId, { status: "blocked" });
      loadSlots();
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Could not block slot.");
    } finally {
      setBusy(false);
    }
  }

  async function removeSlot(slotId: string) {
    const token = getToken();
    if (!token) return;
    setBusy(true);
    setError(null);
    try {
      await deleteOwnerListingSlot(token, listingId, slotId);
      loadSlots();
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Could not delete slot.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className={styles.shareBox}>
      <h2>Availability slots</h2>
      <p className={styles.cardMeta}>
        Add bookable time windows riders will see on the calendar. General notes stay in the
        availability field above.
      </p>
      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}
      {success ? <InlineAlert variant="success">{success}</InlineAlert> : null}

      <form onSubmit={handleCreate} className={styles.slotList}>
        <label>
          Date
          <input name="slot_date" type="date" required />
        </label>
        <label>
          Start time
          <input name="start_time" type="time" required />
        </label>
        <label>
          End time
          <input name="end_time" type="time" required />
        </label>
        <button type="submit" className={styles.button} disabled={busy}>
          Add slot
        </button>
      </form>

      {slots.length === 0 ? (
        <p className={styles.cardMeta}>No upcoming slots yet.</p>
      ) : (
        <div className={styles.slotList}>
          {slots.map((slot) => (
            <div key={slot.id} className={styles.calendarSlotRow}>
              <div>
                <strong>{slot.status}</strong>
                <div className={styles.slotMeta}>{formatSlotRange(slot.start_at, slot.end_at)}</div>
              </div>
              {slot.status === "open" ? (
                <div className={styles.buttonGroup}>
                  <button
                    type="button"
                    className={`${styles.button} ${styles.buttonSecondary}`}
                    disabled={busy}
                    onClick={() => blockSlot(slot.id)}
                  >
                    Block
                  </button>
                  <button
                    type="button"
                    className={`${styles.button} ${styles.buttonDanger}`}
                    disabled={busy}
                    onClick={() => removeSlot(slot.id)}
                  >
                    Delete
                  </button>
                </div>
              ) : null}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
