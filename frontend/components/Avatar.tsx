"use client";

import { useState } from "react";

import styles from "./Avatar.module.css";

export type AvatarSize = "sm" | "md" | "lg";

interface AvatarProps {
  src?: string | null;
  firstName: string;
  lastName?: string | null;
  size?: AvatarSize;
  verified?: boolean;
  alt?: string;
  className?: string;
}

function getInitials(firstName: string, lastName?: string | null): string {
  const first = firstName.trim().charAt(0) ?? "";
  const last = lastName?.trim().charAt(0) ?? "";
  const initials = `${first}${last}`.toUpperCase();
  return initials || "?";
}

export function Avatar({
  src,
  firstName,
  lastName,
  size = "md",
  verified = false,
  alt,
  className,
}: AvatarProps) {
  const [errored, setErrored] = useState(false);
  const showImage = Boolean(src) && !errored;
  const fullName = [firstName, lastName].filter(Boolean).join(" ").trim();
  const resolvedAlt = alt ?? fullName ?? "User avatar";

  return (
    <span className={`${styles.avatar} ${styles[size]} ${className ?? ""}`.trim()}>
      {showImage ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={src as string}
          alt={resolvedAlt}
          className={styles.image}
          onError={() => setErrored(true)}
        />
      ) : (
        <span className={styles.initials} role="img" aria-label={resolvedAlt}>
          {getInitials(firstName, lastName)}
        </span>
      )}
      {verified ? (
        <span className={styles.verifiedBadge} role="img" aria-label="Verified">
          <svg
            viewBox="0 0 16 16"
            aria-hidden="true"
            focusable="false"
            className={styles.verifiedIcon}
          >
            <path
              d="M6.5 10.6 3.9 8l-1.1 1.1 3.7 3.7L13.2 5.7l-1.1-1.1z"
              fill="currentColor"
            />
          </svg>
        </span>
      ) : null}
    </span>
  );
}
