import { AdminUserSummary } from "@/lib/api";

const OAUTH_LABEL: Record<string, string> = {
  google: "Google",
  facebook: "Facebook",
};

const ACTIVITY_LABEL: Record<string, string> = {
  lesson: "Lesson",
  lease: "Lease",
  trail_ride: "Trail ride",
  day_rental: "Day rental",
};

export function formatRoles(
  user: Pick<
    AdminUserSummary,
    | "is_rider"
    | "is_owner"
    | "is_horse_trainer"
    | "is_riding_instructor"
    | "trainer_verified"
  >,
): string {
  const roles: string[] = [];
  if (user.is_rider) roles.push("Rider");
  if (user.is_owner) roles.push("Owner");
  if (user.is_horse_trainer) roles.push("Horse trainer");
  if (user.is_riding_instructor) roles.push("Riding instructor");
  if (user.trainer_verified) roles.push("Verified trainer");
  return roles.length > 0 ? roles.join(" · ") : "—";
}

export function formatTrainerSelfReport(
  user: Pick<AdminUserSummary, "is_horse_trainer" | "is_riding_instructor" | "trainer_verified">,
): string {
  const parts: string[] = [];
  if (user.is_horse_trainer) parts.push("Horse trainer (self-reported)");
  if (user.is_riding_instructor) parts.push("Riding instructor (self-reported)");
  if (user.trainer_verified) parts.push("Verified trainer");
  return parts.length > 0 ? parts.join(" · ") : "—";
}

export function formatAuthMethod(oauthProviders: string[]): string {
  if (oauthProviders.length === 0) {
    return "Password";
  }
  return oauthProviders
    .map((provider) => OAUTH_LABEL[provider] ?? provider)
    .join(", ");
}

export function activityTypeLabel(activityType: string): string {
  return ACTIVITY_LABEL[activityType] ?? activityType.replace(/_/g, " ");
}

export function auditActionLabel(action: string): string {
  const labels: Record<string, string> = {
    verification_status_changed: "Verification changed",
    user_roles_changed: "Roles changed",
    listing_deactivated: "Listing deactivated",
    listing_reactivated: "Listing reactivated",
  };
  return labels[action] ?? action.replace(/_/g, " ");
}
