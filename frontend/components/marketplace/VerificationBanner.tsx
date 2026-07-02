import Link from "next/link";

import { User, VerificationStatus } from "@/lib/api";

import styles from "./marketplace.module.css";

interface VerificationBannerProps {
  user: User;
}

const MESSAGES: Record<VerificationStatus, string> = {
  unverified:
    "Identity verification is required before you can host rides or request bookings.",
  pending: "Your identity verification is pending review. Hosting and bookings are paused.",
  verified: "",
  rejected:
    "Your identity verification was not approved. Contact support if you believe this is an error.",
};

export function VerificationBanner({ user }: VerificationBannerProps) {
  if (user.verification_status === "verified") {
    return null;
  }

  return (
    <div className={styles.banner} role="alert">
      <p>{MESSAGES[user.verification_status]}</p>
      <p className={styles.bannerHint}>
        Sign in with Google or Facebook does not count as identity verification.
      </p>
    </div>
  );
}

interface BlockedActionProps {
  user: User;
  action: string;
}

export function BlockedAction({ user, action }: BlockedActionProps) {
  if (user.verification_status === "verified") {
    return null;
  }

  return (
    <div className={styles.blocked}>
      <p>
        Complete identity verification before you can {action}.
      </p>
      <Link href="/dashboard">Back to dashboard</Link>
    </div>
  );
}
