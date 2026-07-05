"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { PageHeader } from "@/components/marketplace/PageHeader";
import styles from "@/components/marketplace/marketplace.module.css";
import { ThemeToggle } from "@/components/ThemeToggle";
import {
  ApiError,
  FamilyMemberInput,
  FamilyProfile,
  RiderType,
  fetchCurrentUser,
  fetchFamilyProfile,
  updateFamilyProfile,
  updateProfile,
  type User,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

const SKILL_OPTIONS = [
  { value: "", label: "Not set" },
  { value: "1", label: "Self-reported: Beginner" },
  { value: "2", label: "Self-reported: Advanced Beginner" },
  { value: "3", label: "Self-reported: Intermediate" },
  { value: "4", label: "Self-reported: Advanced Intermediate" },
  { value: "5", label: "Self-reported: Professional" },
];

type RosterRow = {
  display_name: string;
  rider_skill_level: string;
  is_minor: boolean;
};

function emptyRoster(size: number): RosterRow[] {
  return Array.from({ length: size }, () => ({
    display_name: "",
    rider_skill_level: "",
    is_minor: false,
  }));
}

export default function SettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isHorseTrainer, setIsHorseTrainer] = useState(false);
  const [isRidingInstructor, setIsRidingInstructor] = useState(false);
  const [riderSkillLevel, setRiderSkillLevel] = useState("");
  const [riderType, setRiderType] = useState<RiderType>("individual");
  const [familyName, setFamilyName] = useState("");
  const [familySize, setFamilySize] = useState(2);
  const [roster, setRoster] = useState<RosterRow[]>(emptyRoster(2));
  const [message, setMessage] = useState<string | null>(null);
  const [familyMessage, setFamilyMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [familyError, setFamilyError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [savingFamily, setSavingFamily] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login?next=/settings");
      return;
    }
    Promise.all([fetchCurrentUser(token), fetchFamilyProfile(token)])
      .then(([u, family]) => {
        setUser(u);
        setIsHorseTrainer(u.is_horse_trainer);
        setIsRidingInstructor(u.is_riding_instructor);
        setRiderSkillLevel(u.rider_skill_level ? String(u.rider_skill_level) : "");
        applyFamilyProfile(family);
      })
      .catch(() => router.replace("/login?next=/settings"));
  }, [router]);

  function applyFamilyProfile(family: FamilyProfile) {
    setRiderType(family.rider_type);
    setFamilyName(family.family_name ?? "");
    setFamilySize(family.family_size ?? 2);
    if (family.rider_type === "family" && family.members.length > 0) {
      setRoster(
        family.members.map((m) => ({
          display_name: m.display_name,
          rider_skill_level: m.rider_skill_level ? String(m.rider_skill_level) : "",
          is_minor: m.is_minor,
        })),
      );
    } else if (family.family_size) {
      setRoster(emptyRoster(family.family_size));
    }
  }

  function handleFamilySizeChange(size: number) {
    const next = Math.min(20, Math.max(2, size));
    setFamilySize(next);
    setRoster((prev) => {
      if (prev.length === next) return prev;
      if (prev.length < next) {
        return [...prev, ...emptyRoster(next - prev.length)];
      }
      return prev.slice(0, next);
    });
  }

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
        rider_skill_level: riderType === "individual" && riderSkillLevel ? Number(riderSkillLevel) : null,
      });
      setUser(updated);
      setMessage("Profile updated.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save profile.");
    } finally {
      setSaving(false);
    }
  }

  async function handleFamilySubmit(event: FormEvent) {
    event.preventDefault();
    const token = getToken();
    if (!token) return;
    setSavingFamily(true);
    setFamilyError(null);
    setFamilyMessage(null);
    try {
      const members: FamilyMemberInput[] | null =
        riderType === "family"
          ? roster.map((row, idx) => ({
              display_name: row.display_name,
              rider_skill_level: row.rider_skill_level ? Number(row.rider_skill_level) : null,
              is_minor: row.is_minor,
              sort_order: idx,
            }))
          : null;
      const updated = await updateFamilyProfile(token, {
        rider_type: riderType,
        family_name: riderType === "family" ? familyName : null,
        family_size: riderType === "family" ? familySize : null,
        members,
      });
      applyFamilyProfile(updated);
      const refreshed = await fetchCurrentUser(token);
      setUser(refreshed);
      setFamilyMessage("Family profile updated.");
    } catch (err) {
      setFamilyError(err instanceof ApiError ? err.message : "Could not save family profile.");
    } finally {
      setSavingFamily(false);
    }
  }

  return (
    <div className={styles.listingsPage}>
      <PageHeader
        title="Settings"
        description="Manage your appearance and self-reported profile claims."
      />

      {user?.is_rider ? (
        <div className={styles.hubSection}>
          <h2 className={styles.hubSectionTitle}>Rider type</h2>
          <p className={styles.cardMeta}>
            Individual riders book for themselves. Family accounts book for a named roster
            (including minors when you are the verified guardian).
          </p>
          {user ? (
            <form className={styles.formStack} onSubmit={handleFamilySubmit}>
              <div className={styles.formStack}>
                <p className={styles.fieldLabel}>Rider type</p>
                <label className={styles.checkboxLabel}>
                  <input
                    type="radio"
                    name="rider_type"
                    checked={riderType === "individual"}
                    onChange={() => setRiderType("individual")}
                  />
                  Individual
                </label>
                <label className={styles.checkboxLabel}>
                  <input
                    type="radio"
                    name="rider_type"
                    checked={riderType === "family"}
                    onChange={() => setRiderType("family")}
                  />
                  Family
                </label>
              </div>

              {riderType === "family" ? (
                <>
                  <label className={styles.fieldLabel}>
                    Family name
                    <input
                      value={familyName}
                      onChange={(e) => setFamilyName(e.target.value)}
                      required
                      maxLength={100}
                    />
                  </label>
                  <label className={styles.fieldLabel}>
                    Number of riders in family
                    <input
                      type="number"
                      min={2}
                      max={20}
                      value={familySize}
                      onChange={(e) => handleFamilySizeChange(Number(e.target.value))}
                      required
                    />
                  </label>
                  <h3 className={styles.hubSectionTitle}>Family roster</h3>
                  {roster.map((row, idx) => (
                    <div key={idx} className={styles.formStack}>
                      <label className={styles.fieldLabel}>
                        Member {idx + 1} name
                        <input
                          value={row.display_name}
                          onChange={(e) =>
                            setRoster((prev) =>
                              prev.map((r, i) =>
                                i === idx ? { ...r, display_name: e.target.value } : r,
                              ),
                            )
                          }
                          required
                          maxLength={100}
                        />
                      </label>
                      <label className={styles.fieldLabel}>
                        Skill level
                        <select
                          value={row.rider_skill_level}
                          onChange={(e) =>
                            setRoster((prev) =>
                              prev.map((r, i) =>
                                i === idx ? { ...r, rider_skill_level: e.target.value } : r,
                              ),
                            )
                          }
                        >
                          {SKILL_OPTIONS.map((opt) => (
                            <option key={opt.value || "none"} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label className={styles.checkboxLabel}>
                        <input
                          type="checkbox"
                          checked={row.is_minor}
                          onChange={(e) =>
                            setRoster((prev) =>
                              prev.map((r, i) =>
                                i === idx ? { ...r, is_minor: e.target.checked } : r,
                              ),
                            )
                          }
                        />
                        Minor (you are the verified guardian)
                      </label>
                    </div>
                  ))}
                </>
              ) : null}

              {familyError ? <p className={styles.errorText}>{familyError}</p> : null}
              {familyMessage ? <p className={styles.successText}>{familyMessage}</p> : null}
              <button type="submit" className={styles.button} disabled={savingFamily}>
                {savingFamily ? "Saving…" : "Save rider type & roster"}
              </button>
            </form>
          ) : (
            <p>Loading profile…</p>
          )}
        </div>
      ) : null}

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
            {riderType === "individual" ? (
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
            ) : (
              <p className={styles.cardMeta}>
                Skill levels for family accounts are set per roster member above.
              </p>
            )}
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
