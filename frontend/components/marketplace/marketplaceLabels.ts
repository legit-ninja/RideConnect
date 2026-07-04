import { ActivityType, VerificationStatus } from "@/lib/api";

const ACTIVITY_LABEL: Record<ActivityType, string> = {
  lesson: "Lesson",
  lease: "Lease",
  trail_ride: "Trail ride",
  day_rental: "Day rental",
};

const FRIEND_STATUS_LABEL: Record<string, string> = {
  pending_owner_confirm: "Awaiting rider",
  pending_guardian: "Awaiting guardian",
  active: "Active",
  declined: "Declined",
  revoked: "Revoked",
};

const BOOKING_STATUS_LABEL: Record<string, string> = {
  pending_owner: "Awaiting owner",
  pending_payment: "Payment pending",
  approved: "Approved",
  declined: "Declined",
  cancelled: "Cancelled",
  completed: "Completed",
};

export function activityTypeLabel(type: ActivityType | string): string {
  return ACTIVITY_LABEL[type as ActivityType] ?? type.replace(/_/g, " ");
}

export function bookingStatusLabel(status: string): string {
  return BOOKING_STATUS_LABEL[status] ?? status.replace(/_/g, " ");
}

export function friendStatusLabel(status: string): string {
  return FRIEND_STATUS_LABEL[status] ?? status.replace(/_/g, " ");
}

export function verificationLabel(status: VerificationStatus): string {
  const labels: Record<VerificationStatus, string> = {
    unverified: "Unverified",
    pending: "Pending review",
    verified: "Verified",
    rejected: "Rejected",
  };
  return labels[status];
}
