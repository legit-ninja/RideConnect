"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { PageHeader } from "@/components/marketplace/PageHeader";
import styles from "@/components/marketplace/marketplace.module.css";
import { ThemeToggle } from "@/components/ThemeToggle";
import { ApiError, fetchCurrentUser, updateProfile, type User } from "@/lib/api";
import { getToken } from "@/lib/auth";

const SKILL_OPTIONS = [
  { value: "", label: "Not set" },
  { value: "1", label: "Self-reported: Beginner" },
  { value: "2", label: "Self-reported: Advanced Beginner" },
  { value: "3", label: "Self-reported: Intermediate" },
  { value: "4", label: "Self-reported: Advanced Intermediate" },
  { value: "5", label: "Self-reported: Professional" },
];

export default function SettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isHorseTrainer, setIsHorseTrainer] = useState(false);
  const [isRidingInstructor, setIsRidingInstructor] = useState(false);
  const [riderSkillLevel, setRiderSkillLevel] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login?next=/settings");
      return;
    }
    fetchCurrentUser(token)
      .then((u) => {
        setUser(u);
        setIsHorseTrainer(u.is_horse_trainer);
        setIsRidingInstructor(u.is_riding_instructor);
        setRiderSkillLevel(u.rider_skill_level ? String(u.rider_skill_level) : "");
      })
      .catch(() => router.replace("/login?next=/settings"));
  }, [router]);

  async function handleProfileSubmit(event: FormEvent) {
    event.preventDefault();
    const token = getToken();
    if (!token) return;
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const updated = await updateProfile(token, {
        is_horse_trainer: isHorseTrainer,
        is_riding_instructor: isRidingInstructor,
        rider_skill_level: riderSkillLevel ? Number(riderSkillLevel) : null,
      });
      setUser(updated);
      setMessage("Profile updated.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save profile.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className={styles.listingsPage}>
      <PageHeader
        title="Settings"
        description="Manage your appearance and self-reported profile claims."
      />

      <div className={styles.hubSection}>
        <h2 className={styles.hubSectionTitle}>Profile claims</h2>
        <p className={styles.cardMeta}>
          Trainer and skill labels are self-reported — not verified credentials unless an
          admin has confirmed trainer status separately.
        </p>
        {user ? (
          <form className={styles.formStack} onSubmit={handleProfileSubmit}>
            <label className={styles.checkboxLabel}>
              <input
                type="checkbox"
                checked={isHorseTrainer}
                onChange={(e) => setIsHorseTrainer(e.target.checked)}
              />
              Self-reported: Horse trainer (trains animals)
            </label>
            <label className={styles.checkboxLabel}>
              <input
                type="checkbox"
                checked={isRidingInstructor}
                onChange={(e) => setIsRidingInstructor(e.target.checked)}
              />
              Self-reported: Riding instructor (teaches people)
            </label>
            <label className={styles.fieldLabel}>
              Rider skill level
              <select
                value={riderSkillLevel}
                onChange={(e) => setRiderSkillLevel(e.target.value)}
              >
                {SKILL_OPTIONS.map((opt) => (
                  <option key={opt.value || "none"} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </label>
            {user.trainer_verified ? (
              <p className={styles.verifiedBadge}>Verified trainer (admin-confirmed)</p>
            ) : null}
            {error ? <p className={styles.errorText}>{error}</p> : null}
            {message ? <p className={styles.successText}>{message}</p> : null}
            <button type="submit" className={styles.button} disabled={saving}>
              {saving ? "Saving…" : "Save profile"}
            </button>
          </form>
        ) : (
          <p>Loading profile…</p>
        )}
      </div>

      <div className={styles.hubSection}>
        <h2 className={styles.hubSectionTitle}>Appearance</h2>
        <ThemeToggle />
      </div>
    </div>
  );
}
