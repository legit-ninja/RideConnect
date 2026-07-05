"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { InlineAlert } from "@/components/marketplace/InlineAlert";
import { LoadingState } from "@/components/marketplace/LoadingState";
import { PageHeader } from "@/components/marketplace/PageHeader";
import {
  activityTypeLabel,
  bookingStatusLabel,
} from "@/components/marketplace/marketplaceLabels";
import styles from "@/components/marketplace/marketplace.module.css";
import {
  ApiError,
  CalendarDaySummary,
  CalendarResponse,
  OpenSlotSummary,
  User,
  fetchCalendar,
  fetchCurrentUser,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function formatMonthYear(year: number, month: number): string {
  return new Date(year, month, 1).toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });
}

function toIsoDate(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function monthRange(year: number, month: number): { from: string; to: string } {
  const from = new Date(year, month, 1);
  const to = new Date(year, month + 1, 0);
  return { from: toIsoDate(from), to: toIsoDate(to) };
}

function buildCalendarCells(year: number, month: number): (Date | null)[] {
  const first = new Date(year, month, 1);
  const last = new Date(year, month + 1, 0);
  const cells: (Date | null)[] = [];
  for (let i = 0; i < first.getDay(); i += 1) {
    cells.push(null);
  }
  for (let day = 1; day <= last.getDate(); day += 1) {
    cells.push(new Date(year, month, day));
  }
  return cells;
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
}

function suitabilityClass(suitability: string): string {
  if (suitability === "poor") return styles.suitabilityPoor;
  if (suitability === "caution") return styles.suitabilityCaution;
  return styles.suitabilityGood;
}

export default function CalendarPage() {
  const router = useRouter();
  const today = new Date();
  const [viewYear, setViewYear] = useState(today.getFullYear());
  const [viewMonth, setViewMonth] = useState(today.getMonth());
  const [user, setUser] = useState<User | null>(null);
  const [data, setData] = useState<CalendarResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState<string>(toIsoDate(today));
  const [showOpen, setShowOpen] = useState(true);
  const [showBookings, setShowBookings] = useState(true);

  const cells = useMemo(
    () => buildCalendarCells(viewYear, viewMonth),
    [viewYear, viewMonth],
  );

  const dayMap = useMemo(() => {
    const map = new Map<string, CalendarDaySummary>();
    data?.days.forEach((day) => map.set(day.date, day));
    return map;
  }, [data]);

  const selectedSlots = useMemo(() => {
    if (!data || !showOpen) return [] as OpenSlotSummary[];
    return data.open_slots.filter(
      (slot) => slot.start_at.slice(0, 10) === selectedDate,
    );
  }, [data, selectedDate, showOpen]);

  const selectedBookings = useMemo(() => {
    if (!data || !showBookings) return [];
    return data.my_bookings.filter(
      (booking) => booking.scheduled_at?.slice(0, 10) === selectedDate,
    );
  }, [data, selectedDate, showBookings]);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    fetchCurrentUser(token)
      .then((currentUser) => {
        if (currentUser.verification_status !== "verified") {
          router.replace("/dashboard");
          return null;
        }
        setUser(currentUser);
        return currentUser;
      })
      .catch(() => {
        router.replace("/login");
      });
  }, [router]);

  useEffect(() => {
    const token = getToken();
    if (!token || !user) return;
    setLoading(true);
    setError(null);
    const { from, to } = monthRange(viewYear, viewMonth);
    fetchCalendar(token, {
      from,
      to,
      include_open_slots: showOpen && user.is_rider,
    })
      .then(setData)
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "Unable to load calendar.");
      })
      .finally(() => setLoading(false));
  }, [viewYear, viewMonth, user, showOpen]);

  function shiftMonth(delta: number) {
    const next = new Date(viewYear, viewMonth + delta, 1);
    setViewYear(next.getFullYear());
    setViewMonth(next.getMonth());
  }

  if (!user) {
    return (
      <div className={styles.listingsPage}>
        <LoadingState label="Loading calendar" />
      </div>
    );
  }

  return (
    <div className={styles.listingsPage}>
      <PageHeader
        title="Ride calendar"
        description="Plan rides with local weather and open availability in your region."
      />

      {error ? <InlineAlert variant="error">{error}</InlineAlert> : null}
      {data?.weather_error ? (
        <InlineAlert variant="warning">{data.weather_error}</InlineAlert>
      ) : null}

      <div className={styles.calendarToolbar}>
        <div className={styles.calendarNav}>
          <button type="button" className={styles.buttonSecondary} onClick={() => shiftMonth(-1)}>
            Previous
          </button>
          <div className={styles.calendarMonthLabel}>
            {formatMonthYear(viewYear, viewMonth)}
          </div>
          <button type="button" className={styles.buttonSecondary} onClick={() => shiftMonth(1)}>
            Next
          </button>
        </div>
        <div className={styles.calendarToggles}>
          {user.is_rider ? (
            <button
              type="button"
              className={showOpen ? styles.chipActive : styles.chip}
              onClick={() => setShowOpen((value) => !value)}
            >
              Open rides
            </button>
          ) : null}
          <button
            type="button"
            className={showBookings ? styles.chipActive : styles.chip}
            onClick={() => setShowBookings((value) => !value)}
          >
            My schedule
          </button>
        </div>
      </div>

      {loading ? (
        <LoadingState label="Loading calendar data" />
      ) : (
        <>
          <div className={styles.calendarGrid}>
            {WEEKDAYS.map((label) => (
              <div key={label} className={styles.calendarWeekday}>
                {label}
              </div>
            ))}
            {cells.map((cell, index) => {
              if (!cell) {
                return <div key={`empty-${index}`} className={styles.calendarDayOutside} />;
              }
              const dateStr = toIsoDate(cell);
              const summary = dayMap.get(dateStr);
              const isSelected = selectedDate === dateStr;
              return (
                <button
                  key={dateStr}
                  type="button"
                  className={[
                    styles.calendarDay,
                    isSelected ? styles.calendarDaySelected : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  onClick={() => setSelectedDate(dateStr)}
                >
                  <span className={styles.calendarDayNumber}>{cell.getDate()}</span>
                  {summary?.weather ? (
                    <span
                      className={`${styles.weatherChip} ${suitabilityClass(summary.weather.ride_suitability)}`}
                    >
                      {summary.weather.temp_max_f != null
                        ? `${Math.round(summary.weather.temp_max_f)}°`
                        : "—"}
                      {summary.weather.precip_probability_max != null
                        ? ` · ${summary.weather.precip_probability_max}% rain`
                        : ""}
                    </span>
                  ) : null}
                  <div className={styles.calendarDayBadges}>
                    {showOpen && summary && summary.open_slot_count > 0 ? (
                      <span className={styles.calendarBadge}>
                        {summary.open_slot_count} open
                      </span>
                    ) : null}
                    {showBookings && summary && summary.my_booking_count > 0 ? (
                      <span className={`${styles.calendarBadge} ${styles.calendarBadgeBooking}`}>
                        {summary.my_booking_count} booked
                      </span>
                    ) : null}
                  </div>
                </button>
              );
            })}
          </div>

          <section className={styles.calendarDayPanel}>
            <h2>
              {new Date(`${selectedDate}T12:00:00`).toLocaleDateString("en-US", {
                weekday: "long",
                month: "long",
                day: "numeric",
              })}
            </h2>

            {dayMap.get(selectedDate)?.weather ? (
              <p className={styles.slotMeta}>
                {dayMap.get(selectedDate)?.weather?.summary} ·{" "}
                {dayMap.get(selectedDate)?.weather?.temp_min_f != null &&
                dayMap.get(selectedDate)?.weather?.temp_max_f != null
                  ? `${Math.round(dayMap.get(selectedDate)!.weather!.temp_min_f!)}–${Math.round(dayMap.get(selectedDate)!.weather!.temp_max_f!)}°F`
                  : "Temperature unavailable"}
                {dayMap.get(selectedDate)?.weather?.wind_speed_max_mph != null
                  ? ` · Wind up to ${Math.round(dayMap.get(selectedDate)!.weather!.wind_speed_max_mph!)} mph`
                  : ""}
              </p>
            ) : null}

            {showOpen && user.is_rider ? (
              <>
                <h3 className={styles.hubSectionTitle}>Open rides</h3>
                {selectedSlots.length === 0 ? (
                  <p className={styles.slotMeta}>No open slots on this day.</p>
                ) : (
                  <div className={styles.slotList}>
                    {selectedSlots.map((slot) => (
                      <div key={slot.id} className={styles.calendarSlotRow}>
                        <div>
                          <strong>{slot.animal_name}</strong>
                          <div className={styles.slotMeta}>
                            {activityTypeLabel(slot.activity_type)} · {slot.display_location}
                          </div>
                          <div className={styles.slotMeta}>
                            {formatTime(slot.start_at)} – {formatTime(slot.end_at)} · ${Number(slot.price).toFixed(2)}
                          </div>
                        </div>
                        <Link
                          href={`/listings/${slot.listing_id}?slot=${slot.id}`}
                          className={styles.button}
                        >
                          Request ride
                        </Link>
                      </div>
                    ))}
                  </div>
                )}
              </>
            ) : null}

            {showBookings ? (
              <>
                <h3 className={styles.hubSectionTitle}>My schedule</h3>
                {selectedBookings.length === 0 ? (
                  <p className={styles.slotMeta}>No rides scheduled on this day.</p>
                ) : (
                  <div className={styles.slotList}>
                    {selectedBookings.map((booking) => (
                      <div key={booking.id} className={styles.calendarBookingRow}>
                        <div>
                          <strong>{booking.animal_name}</strong>
                          <div className={styles.slotMeta}>
                            {activityTypeLabel(booking.activity_type)} ·{" "}
                            {bookingStatusLabel(booking.status)}
                          </div>
                          {booking.scheduled_at ? (
                            <div className={styles.slotMeta}>
                              {formatTime(booking.scheduled_at)}
                            </div>
                          ) : null}
                        </div>
                        <Link href="/rider/bookings" className={styles.buttonSecondary}>
                          View booking
                        </Link>
                      </div>
                    ))}
                  </div>
                )}
              </>
            ) : null}
          </section>
        </>
      )}
    </div>
  );
}
