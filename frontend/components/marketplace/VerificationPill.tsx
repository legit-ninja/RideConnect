import { VerificationStatus } from "@/lib/api";

import styles from "./marketplace.module.css";

const LABEL: Record<VerificationStatus, string> = {
  unverified: "Unverified",
  pending: "Pending review",
  verified: "Verified",
  rejected: "Rejected",
};

const CLASS: Record<VerificationStatus, string> = {
  unverified: styles.badgeUnverified,
  pending: styles.badgePending,
  verified: styles.badgeVerified,
  rejected: styles.badgeRejected,
};

interface VerificationPillProps {
  status: VerificationStatus;
}

export function VerificationPill({ status }: VerificationPillProps) {
  return (
    <span className={`${styles.badge} ${CLASS[status]}`}>{LABEL[status]}</span>
  );
}
