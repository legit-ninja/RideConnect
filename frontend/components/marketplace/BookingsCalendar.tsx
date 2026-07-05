"use client";

import { useMemo, useState } from "react";

import {
  activityTypeLabel,
  bookingStatusLabel,
} from "@/components/marketplace/marketplaceLabels";
import styles from "@/components/marketplace/marketplace.module.css";
import type { BookingRequest } from "@/lib/api";
import { VerificationPill } from "@/components/marketplace/VerificationPill";

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

type DotStatus = "pending" | "approved" | "declined" | "completed" | "cancelled";

const DOT_STATUS_CLASS: Record<DotStatus, string> = {
  pending: styles.statusDotPending,
  approved: styles.statusDotApproved,
  declined: styles.statusDotDeclined,
  completed: styles.statusDotCompleted,
  cancelled: styles.statusDotCancelled,
};

const BADGE_STATUS_CLASS: Record<DotStatus, string> = {
  pending: styles.statusBadgePending,
  approved: styles.statusBadgeApproved,
  declined: styles.statusBadgeDeclined,
  completed: styles.statusBadgeCompleted,
  cancelled: styles.statusBadgeCancelled,
};

const LEGEND: { key: DotStatus; label: string }[] = [
  { key: "pending", label: "Pending" },
  { key: "approved", label: "Approved" },
  { key: "declined", label: "Declined" },
  { key: "completed", label: "Completed" },
  { key: "cancelled", label: "Cancelled" },
];

function toIsoDate(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function formatMonthYear(year: number, month: number): string {
  return new Date(year, month, 1).toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });
}

function buildCalendarCells(year: number, month: number): (number | null)[] {
  const first = new Date(year, month, 1);
  const last = new Date(year, month + 1, 0);
  const cells: (number | null)[] = [];
  for (let i = 0; i < first.getDay(); i += 1) {
    cells.push(null);
  }
  for (let day = 1; day <= last.getDate(); day += 1) {
    cells.push(day);
  }
  return cells;
}

function bookingDotStatus(status: BookingRequest["status"]): DotStatus {
  if (status === "pending_owner" || status === "pending_payment") return "pending";
  if (status === "approved") return "approved";
  if (status === "declined") return "declined";
  if (status === "completed") return "completed";
  return "cancelled";
}

function bookingCalendarDate(booking: BookingRequest): string | null {
  const iso = booking.scheduled_at ?? booking.requested_at;
  return iso ? iso.slice(0, 10) : null;
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
}

export interface BookingsCalendarProps {
  bookings: BookingRequest[];
  onApprove?: (booking: BookingRequest) => void;
  onDecline?: (booking: BookingRequest) => void;
  onComplete?: (booking: BookingRequest) => void;
}

export function BookingsCalendar({
  bookings,
  onApprove,
  onDecline,
  onComplete,
}: BookingsCalendarProps) {
  const today = new Date();
  const [viewYear, setViewYear] = useState(today.getFullYear());
  const [viewMonth, setViewMonth] = useState(today.getMonth());
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  const cells = useMemo(
    () => buildCalendarCells(viewYear, viewMonth),
    [viewYear, viewMonth],
  );

  const bookingsByDate = useMemo(() => {
    const map = new Map<string, BookingRequest[]>();
    for (const booking of bookings) {
      const date = bookingCalendarDate(booking);
      if (!date) continue;
      const list = map.get(date) ?? [];
      list.push(booking);
      map.set(date, list);
    }
    return map;
  }, [bookings]);

  const selectedBookings = selectedDate ? (bookingsByDate.get(selectedDate) ?? []) : [];

  function shiftMonth(delta: number) {
    const next = new Date(viewYear, viewMonth + delta, 1);
    setViewYear(next.getFullYear());
    setViewMonth(next.getMonth());
  }

  function goToday() {
    setViewYear(today.getFullYear());
    setViewMonth(today.getMonth());
    setSelectedDate(toIsoDate(today));
  }

  function handleDayClick(day: number) {
    const dateStr = toIsoDate(new Date(viewYear, viewMonth, day));
    setSelectedDate(dateStr);
  }

  return (
    <div className={styles.bookingsCalendarLayout}>
      <div className={styles.bookingsCalendarMain}>
        <div className={styles.calendarToolbar}>
          <div className={styles.calendarNav}>
            <button
              type="button"
              className={styles.buttonSecondary}
              onClick={() => shiftMonth(-1)}
              aria-label="Previous month"
            >
              Previous
            </button>
            <div className={styles.calendarMonthLabel}>
              {formatMonthYear(viewYear, viewMonth)}
            </div>
            <button
              type="button"
              className={styles.buttonSecondary}
              onClick={() => shiftMonth(1)}
              aria-label="Next month"
            >
              Next
            </button>
          </div>
          <button type="button" className={styles.buttonSecondary} onClick={goToday}>
            Today
          </button>
        </div>

        <div className={styles.calendarGrid}>
          {WEEKDAYS.map((label) => (
            <div key={label} className={styles.calendarWeekday}>
              {label}
            </div>
          ))}
          {cells.map((day, index) => {
            if (day === null) {
              return <div key={`empty-${index}`} className={styles.calendarDayOutside} />;
            }
            const dateStr = toIsoDate(new Date(viewYear, viewMonth, day));
            const dayBookings = bookingsByDate.get(dateStr) ?? [];
            const isToday =
              today.getFullYear() === viewYear &&
              today.getMonth() === viewMonth &&
              today.getDate() === day;
            const isSelected = selectedDate === dateStr;

            return (
              <button
                key={dateStr}
                type="button"
                className={[
                  styles.calendarDay,
                  styles.bookingsCalendarDay,
                  isSelected ? styles.calendarDaySelected : "",
                  isToday && !isSelected ? styles.calendarDayToday : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                onClick={() => handleDayClick(day)}
              >
                <span className={styles.calendarDayNumber}>{day}</span>
                {dayBookings.length > 0 ? (
                  <div className={styles.calendarStatusDots}>
                    {dayBookings.slice(0, 3).map((booking) => (
                      <span
                        key={booking.id}
                        className={`${styles.statusDot} ${DOT_STATUS_CLASS[bookingDotStatus(booking.status)]}`}
                        aria-hidden="true"
                      />
                    ))}
                    {dayBookings.length > 3 ? (
                      <span className={styles.calendarDotOverflow}>
                        +{dayBookings.length - 3}
                      </span>
                    ) : null}
                  </div>
                ) : null}
              </button>
            );
          })}
        </div>

        <div className={styles.calendarLegend}>
          {LEGEND.map(({ key, label }) => (
            <span key={key} className={styles.calendarLegendItem}>
              <span className={`${styles.statusDot} ${DOT_STATUS_CLASS[key]}`} aria-hidden="true" />
              {label}
            </span>
          ))}
        </div>
      </div>

      <aside className={styles.bookingsCalendarSide}>
        <h2 className={styles.bookingsCalendarSideTitle}>
          {selectedDate
            ? new Date(`${selectedDate}T12:00:00`).toLocaleDateString("en-US", {
                weekday: "long",
                month: "long",
                day: "numeric",
              })
            : "Select a date"}
        </h2>

        {!selectedDate ? (
          <p className={styles.slotMeta}>
            Click any day on the calendar to see booking requests scheduled for that date.
          </p>
        ) : selectedBookings.length === 0 ? (
          <p className={styles.slotMeta}>No booking requests for this date.</p>
        ) : (
          <div className={styles.slotList}>
            {selectedBookings.map((booking) => {
              const dotStatus = bookingDotStatus(booking.status);
              const canRespond =
                booking.status === "pending_owner" || booking.status === "pending_payment";
              return (
                <article key={booking.id} className={styles.bookingsCalendarCard}>
                  <div>
                    <strong>
                      {booking.animal_name} — {activityTypeLabel(booking.activity_type)}
                    </strong>
                    <div className={styles.slotMeta}>From {booking.rider_email}</div>
                    <VerificationPill status={booking.rider_verification_status} />
                    {booking.scheduled_at ? (
                      <div className={styles.slotMeta}>Time: {formatTime(booking.scheduled_at)}</div>
                    ) : null}
                    {booking.note ? (
                      <div className={styles.slotMeta}>Note: {booking.note}</div>
                    ) : null}
                    <span
                      className={`${styles.statusBadge} ${BADGE_STATUS_CLASS[dotStatus]}`}
                    >
                      {bookingStatusLabel(booking.status)}
                    </span>
                  </div>
                  {canRespond && onApprove && onDecline ? (
                    <div className={styles.buttonGroup}>
                      <button
                        type="button"
                        className={styles.button}
                        onClick={() => onApprove(booking)}
                      >
                        Approve
                      </button>
                      <button
                        type="button"
                        className={styles.buttonSecondary}
                        onClick={() => onDecline(booking)}
                      >
                        Decline
                      </button>
                    </div>
                  ) : booking.status === "approved" && onComplete ? (
                    <button
                      type="button"
                      className={styles.buttonSecondary}
                      onClick={() => onComplete(booking)}
                    >
                      Mark complete
                    </button>
                  ) : null}
                </article>
              );
            })}
          </div>
        )}
      </aside>
    </div>
  );
}
