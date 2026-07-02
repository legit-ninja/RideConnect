"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import styles from "../auth.module.css";
import { ApiError, fetchCurrentUser, loginUser } from "@/lib/api";
import { setToken } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const tokenResponse = await loginUser({ email, password });
      setToken(tokenResponse.access_token);
      const user = await fetchCurrentUser(tokenResponse.access_token);
      router.push(user.is_admin ? "/admin" : "/dashboard");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Unable to sign in. Is the API running?");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.authForm}>
      <h1>Sign in</h1>
      <p>Use your RideConnect account or admin credentials.</p>
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
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        {error ? <p className={styles.error}>{error}</p> : null}
        <button className={styles.button} type="submit" disabled={loading}>
          {loading ? "Signing in…" : "Sign in"}
        </button>
      </form>
      <p className={styles.linkRow}>
        No account? <Link href="/register">Create one</Link>
      </p>
    </div>
  );
}
