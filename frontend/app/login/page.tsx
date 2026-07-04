"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";

import styles from "../auth.module.css";
import { ApiError, fetchCurrentUser, loginUser } from "@/lib/api";
import { setToken } from "@/lib/auth";
import { buildAuthQuery, postAuthPath } from "@/lib/funnel";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const src = searchParams.get("src");
  const ref = searchParams.get("ref");
  const next = searchParams.get("next");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const registerHref = `/register${buildAuthQuery({ src, ref, next })}`;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const tokenResponse = await loginUser({ email, password });
      setToken(tokenResponse.access_token);
      const user = await fetchCurrentUser(tokenResponse.access_token);
      router.push(
        postAuthPath({ src, ref, next, isAdmin: user.is_admin }),
      );
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
        No account? <Link href={registerHref}>Create one</Link>
      </p>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<p className={styles.authForm}>Loading…</p>}>
      <LoginForm />
    </Suspense>
  );
}
