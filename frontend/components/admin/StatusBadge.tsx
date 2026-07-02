import { VerificationStatus } from "@/lib/api";

import styles from "./admin.module.css";

const VERIFICATION_LABEL: Record<VerificationStatus, string> = {
  unverified: "Unverified",
  pending: "Pending review",
  verified: "Verified",
  rejected: "Rejected",
};

const VERIFICATION_CLASS: Record<VerificationStatus, string> = {
  unverified: styles.badgeUnverified,
  pending: styles.badgePending,
  verified: styles.badgeVerified,
  rejected: styles.badgeRejected,
};

interface StatusBadgeProps {
  kind: "verification";
  status: VerificationStatus;
}

interface ListingStatusBadgeProps {
  kind: "listing";
  active: boolean;
}

type Props = StatusBadgeProps | ListingStatusBadgeProps;

export function StatusBadge(props: Props) {
  if (props.kind === "verification") {
    return (
      <span
        className={`${styles.badge} ${VERIFICATION_CLASS[props.status]}`}
      >
        {VERIFICATION_LABEL[props.status]}
      </span>
    );
  }

  return (
    <span
      className={`${styles.badge} ${
        props.active ? styles.badgeActive : styles.badgeInactive
      }`}
    >
      {props.active ? "Active" : "Inactive"}
    </span>
  );
}
