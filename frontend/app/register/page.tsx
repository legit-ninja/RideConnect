"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";

import styles from "../auth.module.css";
import { ApiError, registerUser } from "@/lib/api";
import { buildAuthQuery } from "@/lib/funnel";

function RegisterForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const src = searchParams.get("src");
  const ref = searchParams.get("ref");
  const next = searchParams.get("next");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [isRider, setIsRider] = useState(true);
  const [isOwner, setIsOwner] = useState(true);
  const [isTrainer, setIsTrainer] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const loginHref = `/login${buildAuthQuery({ src, ref, next })}`;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await registerUser(
        {
          email,
          password,
          first_name: firstName,
          last_name: lastName,
          is_rider: isRider,
          is_owner: isOwner,
          is_trainer: isTrainer,
        },
        { src: src ?? undefined, ref: ref ?? undefined },
      );
      router.push(`${loginHref}${loginHref.includes("?") ? "&" : "?"}registered=1`);
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
      <p>Register as a rider, owner, trainer, or any combination. Verification is required before ride activity.</p>
      <form className={styles.authForm} onSubmit={handleSubmit}>
        <div className={styles.field}>
          <label htmlFor="first_name">First name</label>
          <input
            id="first_name"
            required
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
          />
        </div>
        <div className={styles.field}>
          <label htmlFor="last_name">Last name</label>
          <input
            id="last_name"
            required
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
          />
        </div>
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
          <label>
            <input
              type="checkbox"
              checked={isTrainer}
              onChange={(e) => setIsTrainer(e.target.checked)}
            />
            I am a trainer
          </label>
        </div>
        {error ? <p className={styles.error}>{error}</p> : null}
        <button className={styles.button} type="submit" disabled={loading}>
          {loading ? "Creating account…" : "Create account"}
        </button>
      </form>
      <p className={styles.linkRow}>
        Already have an account? <Link href={loginHref}>Sign in</Link>
      </p>
    </div>
  );
}

export default function RegisterPage() {
  return (
    <Suspense fallback={<p className={styles.authForm}>Loading…</p>}>
      <RegisterForm />
    </Suspense>
  );
}
