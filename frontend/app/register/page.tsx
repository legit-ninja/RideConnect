"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import styles from "../auth.module.css";
import { ApiError, registerUser } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isRider, setIsRider] = useState(true);
  const [isOwner, setIsOwner] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await registerUser({
        email,
        password,
        is_rider: isRider,
        is_owner: isOwner,
      });
      router.push("/login?registered=1");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Unable to create account. Is the API running?");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.authForm}>
      <h1>Create account</h1>
      <p>Register as a rider, owner, or both. Verification is required before ride activity.</p>
      <form className={styles.authForm} onSubmit={handleSubmit}>
        <div className={styles.field}>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className={styles.field}>
          <label htmlFor="password">Password (min 8 characters)</label>
          <input
            id="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <div className={styles.checkboxRow}>
          <label>
            <input
              type="checkbox"
              checked={isRider}
              onChange={(e) => setIsRider(e.target.checked)}
            />
            I am a rider
          </label>
          <label>
            <input
              type="checkbox"
              checked={isOwner}
              onChange={(e) => setIsOwner(e.target.checked)}
            />
            I am an owner
          </label>
        </div>
        {error ? <p className={styles.error}>{error}</p> : null}
        <button className={styles.button} type="submit" disabled={loading}>
          {loading ? "Creating account…" : "Create account"}
        </button>
      </form>
      <p className={styles.linkRow}>
        Already have an account? <Link href="/login">Sign in</Link>
      </p>
    </div>
  );
}
