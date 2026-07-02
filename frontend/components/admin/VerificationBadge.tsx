import { VerificationStatus } from "@/lib/api";

import { StatusBadge } from "./StatusBadge";

interface VerificationBadgeProps {
  status: VerificationStatus;
}

export function VerificationBadge({ status }: VerificationBadgeProps) {
  return <StatusBadge kind="verification" status={status} />;
}
