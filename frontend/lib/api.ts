const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type VerificationStatus =
  | "unverified"
  | "pending"
  | "verified"
  | "rejected";

export interface User {
  id: string;
  email: string;
  is_rider: boolean;
  is_owner: boolean;
  is_horse_trainer: boolean;
  is_riding_instructor: boolean;
  trainer_verified: boolean;
  rider_skill_level: number | null;
  is_admin: boolean;
  verification_status: VerificationStatus;
  is_minor: boolean;
  created_at: string;
  first_name: string;
  last_name: string;
  avatar_url?: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export type ActivityType = "lesson" | "lease" | "trail_ride" | "day_rental";

export type RidingStyle = "western" | "english" | "therapy";

export interface Species {
  id: string;
  name: string;
  active_in_ui: boolean;
}

export interface ListingSummary {
  id: string;
  animal_id: string;
  animal_name: string;
  species_id: string;
  activity_type: ActivityType;
  price: string;
  availability: string | null;
  friend_only_allowed: boolean;
  slug: string;
  display_location: string;
  public_lat: number;
  public_lng: number;
  photo_urls: string[];
  riding_styles: RidingStyle[];
  created_at: string;
}

export interface ListingDetail extends ListingSummary {
  owner_id: string;
  description: string | null;
  breed: string | null;
  active: boolean;
}

export interface Animal {
  id: string;
  owner_id: string;
  species_id: string;
  name: string;
  breed: string | null;
  age: number | null;
  description: string | null;
  lat: number;
  lng: number;
  address: string;
  photo_urls: string[];
  riding_styles: RidingStyle[];
  created_at: string;
}

export interface OwnerListing {
  id: string;
  animal_id: string;
  owner_id: string;
  activity_type: ActivityType;
  price: string;
  availability: string | null;
  friend_only_allowed: boolean;
  active: boolean;
  slug: string;
  display_location: string;
  min_rider_skill: number | null;
  max_rider_weight_lbs: number | null;
  helmet_required: boolean;
  tack_provided: string;
  created_at: string;
}

export interface AdminStats {
  total_users: number;
  admin_users: number;
  verified_users: number;
  unverified_users: number;
  pending_users: number;
  rejected_users: number;
  rider_users: number;
  owner_users: number;
  oauth_users: number;
  signups_last_7d: number;
  total_animals: number;
  total_listings: number;
  active_listings: number;
}

export interface AdminListingSummary {
  id: string;
  animal_name: string;
  owner_email: string;
  activity_type: string;
  price: string;
  availability: string | null;
  active: boolean;
  created_at: string;
}

export interface AdminListingListResponse {
  items: AdminListingSummary[];
  total: number;
}

export interface AdminUserSummary {
  id: string;
  email: string;
  is_rider: boolean;
  is_owner: boolean;
  is_horse_trainer: boolean;
  is_riding_instructor: boolean;
  trainer_verified: boolean;
  rider_skill_level: number | null;
  is_admin: boolean;
  verification_status: VerificationStatus;
  is_minor: boolean;
  oauth_providers: string[];
  created_at: string;
}

export interface OAuthAccountSummary {
  provider: string;
  provider_email: string | null;
  provider_email_verified: boolean;
  created_at: string;
}

export interface AdminGuardianSummary {
  id: string;
  email: string;
  verification_status: VerificationStatus;
}

export interface AdminUserDetail extends AdminUserSummary {
  phone: string | null;
  guardian_user_id: string | null;
  guardian: AdminGuardianSummary | null;
  oauth_accounts: OAuthAccountSummary[];
  animal_count: number;
  listing_count: number;
  active_listing_count: number;
}

export interface AdminAuditLogEntry {
  id: string;
  actor_id: string;
  actor_email: string;
  action: string;
  target_user_id: string | null;
  target_user_email: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface AdminAuditLogListResponse {
  items: AdminAuditLogEntry[];
  total: number;
  limit: number;
  offset: number;
}

export interface AdminUserListResponse {
  items: AdminUserSummary[];
  total: number;
  limit: number;
  offset: number;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function parseError(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: string | { msg: string }[] };
    if (typeof data.detail === "string") {
      return data.detail;
    }
    if (Array.isArray(data.detail) && data.detail[0]?.msg) {
      return data.detail[0].msg;
    }
  } catch {
    // ignore parse errors
  }
  return "Request failed";
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null,
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    throw new ApiError(await parseError(response), response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function registerUser(
  payload: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    is_rider: boolean;
    is_owner: boolean;
  },
  funnel?: { src?: string; ref?: string },
): Promise<User> {
  const search = new URLSearchParams();
  if (funnel?.src) search.set("src", funnel.src);
  if (funnel?.ref) search.set("ref", funnel.ref);
  const query = search.toString();
  const path = query ? `/auth/register?${query}` : "/auth/register";
  return request<User>(path, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function loginUser(payload: {
  email: string;
  password: string;
}): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchCurrentUser(token: string): Promise<User> {
  return request<User>("/auth/me", {}, token);
}

export function updateProfile(
  token: string,
  payload: {
    is_horse_trainer?: boolean;
    is_riding_instructor?: boolean;
    rider_skill_level?: number | null;
  },
): Promise<User> {
  return request<User>(
    "/auth/me/profile",
    { method: "PATCH", body: JSON.stringify(payload) },
    token,
  );
}

export function fetchAdminStats(token: string): Promise<AdminStats> {
  return request<AdminStats>("/admin/stats", {}, token);
}

export function fetchAdminUsers(
  token: string,
  params: {
    q?: string;
    verification_status?: VerificationStatus;
    is_admin?: boolean;
    limit?: number;
    offset?: number;
  } = {},
): Promise<AdminUserListResponse> {
  const search = new URLSearchParams();
  if (params.q) search.set("q", params.q);
  if (params.verification_status) {
    search.set("verification_status", params.verification_status);
  }
  if (params.is_admin !== undefined) {
    search.set("is_admin", String(params.is_admin));
  }
  if (params.limit !== undefined) search.set("limit", String(params.limit));
  if (params.offset !== undefined) search.set("offset", String(params.offset));
  const query = search.toString();
  const path = query ? `/admin/users?${query}` : "/admin/users";
  return request<AdminUserListResponse>(path, {}, token);
}

export function fetchAdminUser(
  token: string,
  userId: string,
): Promise<AdminUserDetail> {
  return request<AdminUserDetail>(`/admin/users/${userId}`, {}, token);
}

export function updateUserVerification(
  token: string,
  userId: string,
  payload: { verification_status: VerificationStatus; note?: string },
): Promise<AdminUserDetail> {
  return request<AdminUserDetail>(
    `/admin/users/${userId}/verification`,
    { method: "PATCH", body: JSON.stringify(payload) },
    token,
  );
}

export function updateUserRoles(
  token: string,
  userId: string,
  payload: { is_rider: boolean; is_owner: boolean },
): Promise<AdminUserDetail> {
  return request<AdminUserDetail>(
    `/admin/users/${userId}/roles`,
    { method: "PATCH", body: JSON.stringify(payload) },
    token,
  );
}

export function updateTrainerVerification(
  token: string,
  userId: string,
  payload: { trainer_verified: boolean; note?: string },
): Promise<AdminUserDetail> {
  return request<AdminUserDetail>(
    `/admin/users/${userId}/trainer-verification`,
    { method: "PATCH", body: JSON.stringify(payload) },
    token,
  );
}

export function fetchSpecies(): Promise<Species[]> {
  return request<Species[]>("/species");
}

export function fetchListings(params: {
  activity_type?: ActivityType;
  species_id?: string;
  min_price?: number;
  max_price?: number;
  riding_style?: RidingStyle;
} = {}): Promise<ListingSummary[]> {
  const search = new URLSearchParams();
  if (params.activity_type) search.set("activity_type", params.activity_type);
  if (params.species_id) search.set("species_id", params.species_id);
  if (params.min_price !== undefined) search.set("min_price", String(params.min_price));
  if (params.max_price !== undefined) search.set("max_price", String(params.max_price));
  if (params.riding_style) search.set("riding_style", params.riding_style);
  const query = search.toString();
  const path = query ? `/listings?${query}` : "/listings";
  return request<ListingSummary[]>(path);
}

export function fetchListing(id: string, token?: string | null): Promise<ListingDetail> {
  return request<ListingDetail>(`/listings/${id}`, {}, token);
}

export function fetchListingOpenSlots(
  token: string,
  listingId: string,
): Promise<AvailabilitySlot[]> {
  return request<AvailabilitySlot[]>(`/listings/${listingId}/slots`, {}, token);
}

export function fetchOwnerAnimals(token: string): Promise<Animal[]> {
  return request<Animal[]>("/owner/animals", {}, token);
}

export function createOwnerAnimal(
  token: string,
  payload: Omit<Animal, "id" | "owner_id" | "created_at">,
): Promise<Animal> {
  return request<Animal>(
    "/owner/animals",
    { method: "POST", body: JSON.stringify(payload) },
    token,
  );
}

export function updateOwnerAnimal(
  token: string,
  id: string,
  payload: Partial<Omit<Animal, "id" | "owner_id" | "created_at">>,
): Promise<Animal> {
  return request<Animal>(
    `/owner/animals/${id}`,
    { method: "PATCH", body: JSON.stringify(payload) },
    token,
  );
}

export function fetchOwnerListings(token: string): Promise<OwnerListing[]> {
  return request<OwnerListing[]>("/owner/listings", {}, token);
}

export function createOwnerListing(
  token: string,
  payload: {
    animal_id: string;
    activity_type: ActivityType;
    price: number;
    availability?: string;
    friend_only_allowed?: boolean;
    active?: boolean;
    min_rider_skill?: number | null;
    max_rider_weight_lbs?: number | null;
    helmet_required?: boolean;
    tack_provided?: string;
  },
): Promise<OwnerListing> {
  return request<OwnerListing>(
    "/owner/listings",
    { method: "POST", body: JSON.stringify(payload) },
    token,
  );
}

export function updateOwnerListing(
  token: string,
  id: string,
  payload: Partial<{
    activity_type: ActivityType;
    price: number;
    availability: string;
    friend_only_allowed: boolean;
    active: boolean;
    min_rider_skill: number | null;
    max_rider_weight_lbs: number | null;
    helmet_required: boolean;
    tack_provided: string;
  }>,
): Promise<OwnerListing> {
  return request<OwnerListing>(
    `/owner/listings/${id}`,
    { method: "PATCH", body: JSON.stringify(payload) },
    token,
  );
}

export function fetchAdminListings(
  token: string,
  params: { active?: boolean; owner_id?: string } = {},
): Promise<AdminListingListResponse> {
  const search = new URLSearchParams();
  if (params.active !== undefined) search.set("active", String(params.active));
  if (params.owner_id) search.set("owner_id", params.owner_id);
  const query = search.toString();
  const path = query ? `/admin/listings?${query}` : "/admin/listings";
  return request<AdminListingListResponse>(path, {}, token);
}

export function fetchAdminAudit(
  token: string,
  params: {
    actor_id?: string;
    target_user_id?: string;
    action?: string;
    limit?: number;
    offset?: number;
  } = {},
): Promise<AdminAuditLogListResponse> {
  const search = new URLSearchParams();
  if (params.actor_id) search.set("actor_id", params.actor_id);
  if (params.target_user_id) search.set("target_user_id", params.target_user_id);
  if (params.action) search.set("action", params.action);
  if (params.limit !== undefined) search.set("limit", String(params.limit));
  if (params.offset !== undefined) search.set("offset", String(params.offset));
  const query = search.toString();
  const path = query ? `/admin/audit?${query}` : "/admin/audit";
  return request<AdminAuditLogListResponse>(path, {}, token);
}

export function updateAdminListingActive(
  token: string,
  listingId: string,
  active: boolean,
): Promise<AdminListingSummary> {
  return request<AdminListingSummary>(
    `/admin/listings/${listingId}`,
    { method: "PATCH", body: JSON.stringify({ active }) },
    token,
  );
}

export type FriendInviteStatus =
  | "pending_owner_confirm"
  | "pending_guardian"
  | "active"
  | "declined"
  | "revoked";

export interface FriendInvite {
  id: string;
  owner_id: string;
  rider_id: string | null;
  invitee_email: string;
  status: FriendInviteStatus;
  invited_at: string;
  accepted_at: string | null;
  created_at: string;
}

export interface FriendInviteListResponse {
  items: FriendInvite[];
}

export type BookingStatus =
  | "pending_owner"
  | "pending_payment"
  | "approved"
  | "declined"
  | "cancelled"
  | "completed";

export type PaymentType = "paid" | "free";

export interface BookingRequest {
  id: string;
  listing_id: string;
  animal_name: string;
  rider_id: string;
  rider_email: string;
  rider_verification_status: VerificationStatus;
  owner_id: string;
  owner_email: string;
  payment_type: PaymentType;
  status: BookingStatus;
  scheduled_at: string | null;
  availability_slot_id?: string | null;
  note: string | null;
  requested_at: string;
  listing_price: string;
  activity_type: string;
  thread_id?: string | null;
  rider_skill_warning?: string | null;
}

export interface BookingListResponse {
  items: BookingRequest[];
  total: number;
}

export function fetchOwnerFriendInvites(token: string): Promise<FriendInviteListResponse> {
  return request<FriendInviteListResponse>("/owner/friend-invites", {}, token);
}

export function createFriendInvite(
  token: string,
  payload: { invitee_email: string },
): Promise<FriendInvite> {
  return request<FriendInvite>(
    "/owner/friend-invites",
    { method: "POST", body: JSON.stringify(payload) },
    token,
  );
}

export function cancelFriendInvite(token: string, inviteId: string): Promise<FriendInvite> {
  return request<FriendInvite>(
    `/owner/friend-invites/${inviteId}`,
    { method: "PATCH", body: JSON.stringify({ status: "revoked" }) },
    token,
  );
}

export function fetchRiderFriendInvites(token: string): Promise<FriendInviteListResponse> {
  return request<FriendInviteListResponse>("/rider/friend-invites", {}, token);
}

export function respondFriendInvite(
  token: string,
  inviteId: string,
  status: "accepted" | "declined",
): Promise<FriendInvite> {
  return request<FriendInvite>(
    `/rider/friend-invites/${inviteId}/respond`,
    { method: "PATCH", body: JSON.stringify({ status }) },
    token,
  );
}

export function createBooking(
  token: string,
  payload: {
    listing_id: string;
    availability_slot_id?: string;
    note?: string;
  },
): Promise<BookingRequest> {
  return request<BookingRequest>(
    "/bookings",
    { method: "POST", body: JSON.stringify(payload) },
    token,
  );
}

export function fetchBookings(
  token: string,
  role: "rider" | "owner" = "rider",
): Promise<BookingListResponse> {
  return request<BookingListResponse>(`/bookings?role=${role}`, {}, token);
}

export function updateBookingStatus(
  token: string,
  bookingId: string,
  status: "approved" | "declined" | "cancelled" | "completed",
): Promise<BookingRequest> {
  return request<BookingRequest>(
    `/bookings/${bookingId}`,
    { method: "PATCH", body: JSON.stringify({ status }) },
    token,
  );
}

export function fetchAdminBookings(
  token: string,
  params: { limit?: number; offset?: number } = {},
): Promise<BookingListResponse> {
  const search = new URLSearchParams();
  if (params.limit !== undefined) search.set("limit", String(params.limit));
  if (params.offset !== undefined) search.set("offset", String(params.offset));
  const query = search.toString();
  const path = query ? `/admin/bookings?${query}` : "/admin/bookings";
  return request<BookingListResponse>(path, {}, token);
}

export interface PublicListing {
  animal_name: string;
  species: string;
  breed: string | null;
  age: number | null;
  photo_urls: string[];
  activity_type: ActivityType;
  price: string | null;
  display_location: string;
  public_lat: number;
  public_lng: number;
  owner_first_name: string;
  owner_last_initial: string;
  owner_verified: boolean;
  owner_trainer_verified: boolean;
  owner_member_since: string;
  review_count: number;
  review_average: number | null;
  riding_styles: RidingStyle[];
  slug: string;
  active: boolean;
  min_rider_skill: number | null;
  min_rider_skill_label: string | null;
  max_rider_weight_lbs: number | null;
  helmet_required: boolean;
  tack_provided: string;
  tack_provided_label: string;
}

export interface PublicInvitePreview {
  owner_first_name: string;
  owner_verified: boolean;
  animal_names: string[];
  token_valid: boolean;
  expired: boolean;
  revoked: boolean;
}

export interface InviteToken {
  id: string;
  token: string;
  animal_id: string | null;
  max_uses: number;
  use_count: number;
  expires_at: string;
  revoked_at: string | null;
  created_at: string;
  share_url: string;
}

export interface InviteTokenListResponse {
  items: InviteToken[];
}

export interface AdminPlatformFlag {
  id: string;
  user_id: string;
  user_email: string;
  flag_type: string;
  details: Record<string, unknown> | null;
  created_at: string;
  resolved_at: string | null;
}

export interface AdminPlatformFlagListResponse {
  items: AdminPlatformFlag[];
  total: number;
}

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export function publicListingUrl(slug: string): string {
  return `${SITE_URL}/l/${slug}`;
}

export function fetchPublicListing(slug: string): Promise<PublicListing> {
  return request<PublicListing>(`/public/listings/${slug}`);
}

export function fetchPublicInvite(token: string): Promise<PublicInvitePreview> {
  return request<PublicInvitePreview>(`/public/invites/${token}`);
}

export function createInviteToken(
  token: string,
  payload: { animal_id?: string; max_uses?: number; expires_in_days?: number } = {},
): Promise<InviteToken> {
  return request<InviteToken>(
    "/invites/tokens",
    { method: "POST", body: JSON.stringify(payload) },
    token,
  );
}

export function fetchInviteTokens(token: string): Promise<InviteTokenListResponse> {
  return request<InviteTokenListResponse>("/invites/tokens", {}, token);
}

export function revokeInviteToken(token: string, tokenId: string): Promise<void> {
  return request<void>(`/invites/tokens/${tokenId}`, { method: "DELETE" }, token);
}

export function redeemInviteToken(
  token: string,
  inviteToken: string,
): Promise<{ friend_invite_id: string; status: string }> {
  return request(`/invites/tokens/${inviteToken}/redeem`, { method: "POST" }, token);
}

export function confirmFriendInvite(
  token: string,
  inviteId: string,
  action: "confirm" | "decline",
): Promise<{ status: string }> {
  return request(
    `/invites/${inviteId}/confirm`,
    { method: "POST", body: JSON.stringify({ action }) },
    token,
  );
}

export function guardianApproveInvite(
  token: string,
  inviteId: string,
): Promise<{ status: string }> {
  return request(`/invites/${inviteId}/guardian-approve`, { method: "POST" }, token);
}

export function createBookingReview(
  token: string,
  bookingId: string,
  payload: { rating: number; body?: string },
): Promise<{ id: string; rating: number }> {
  return request(
    `/bookings/${bookingId}/reviews`,
    { method: "POST", body: JSON.stringify(payload) },
    token,
  );
}

export function fetchAdminFlags(token: string): Promise<AdminPlatformFlagListResponse> {
  return request<AdminPlatformFlagListResponse>("/admin/flags", {}, token);
}

export async function uploadListingPhoto(
  token: string,
  listingId: string,
  file: File,
): Promise<{ id: string; url: string; thumbnail_url: string }> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${API_URL}/owner/listings/${listingId}/photos`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  if (!response.ok) {
    throw new ApiError(await parseError(response), response.status);
  }
  return (await response.json()) as { id: string; url: string; thumbnail_url: string };
}

export function logClientEvent(
  payload: {
    event_type: string;
    src?: string;
    listing_slug?: string;
    invite_token?: string;
  },
  token?: string | null,
): Promise<void> {
  return request<void>(
    "/events",
    { method: "POST", body: JSON.stringify(payload) },
    token,
  );
}

export interface AvailabilitySlot {
  id: string;
  listing_id: string;
  start_at: string;
  end_at: string;
  status: string;
  capacity: number;
  created_at: string;
}

export interface CalendarWeatherDay {
  date: string;
  temp_max_f: number | null;
  temp_min_f: number | null;
  precip_probability_max: number | null;
  wind_speed_max_mph: number | null;
  weather_code: number | null;
  ride_suitability: "good" | "caution" | "poor";
  summary: string;
}

export interface CalendarDaySummary {
  date: string;
  open_slot_count: number;
  my_booking_count: number;
  weather: CalendarWeatherDay | null;
}

export interface OpenSlotSummary {
  id: string;
  listing_id: string;
  slug: string;
  animal_name: string;
  activity_type: ActivityType;
  price: string;
  display_location: string;
  start_at: string;
  end_at: string;
}

export interface CalendarResponse {
  days: CalendarDaySummary[];
  open_slots: OpenSlotSummary[];
  my_bookings: BookingRequest[];
  weather_error: string | null;
}

export function fetchCalendar(
  token: string,
  params: {
    from: string;
    to: string;
    lat?: number;
    lng?: number;
    radius_km?: number;
    include_open_slots?: boolean;
  },
): Promise<CalendarResponse> {
  const search = new URLSearchParams();
  search.set("from", params.from);
  search.set("to", params.to);
  if (params.lat !== undefined) search.set("lat", String(params.lat));
  if (params.lng !== undefined) search.set("lng", String(params.lng));
  if (params.radius_km !== undefined) search.set("radius_km", String(params.radius_km));
  if (params.include_open_slots !== undefined) {
    search.set("include_open_slots", String(params.include_open_slots));
  }
  return request<CalendarResponse>(`/calendar?${search.toString()}`, {}, token);
}

export function fetchOwnerListingSlots(
  token: string,
  listingId: string,
  params: { from?: string; to?: string } = {},
): Promise<AvailabilitySlot[]> {
  const search = new URLSearchParams();
  if (params.from) search.set("from", params.from);
  if (params.to) search.set("to", params.to);
  const query = search.toString();
  const path = query
    ? `/owner/listings/${listingId}/slots?${query}`
    : `/owner/listings/${listingId}/slots`;
  return request<AvailabilitySlot[]>(path, {}, token);
}

export function createOwnerListingSlot(
  token: string,
  listingId: string,
  payload: { start_at: string; end_at: string; capacity?: number },
): Promise<AvailabilitySlot> {
  return request<AvailabilitySlot>(
    `/owner/listings/${listingId}/slots`,
    { method: "POST", body: JSON.stringify(payload) },
    token,
  );
}

export function updateOwnerListingSlot(
  token: string,
  listingId: string,
  slotId: string,
  payload: { start_at?: string; end_at?: string; status?: "open" | "blocked" },
): Promise<AvailabilitySlot> {
  return request<AvailabilitySlot>(
    `/owner/listings/${listingId}/slots/${slotId}`,
    { method: "PATCH", body: JSON.stringify(payload) },
    token,
  );
}

export function deleteOwnerListingSlot(
  token: string,
  listingId: string,
  slotId: string,
): Promise<void> {
  return request<void>(
    `/owner/listings/${listingId}/slots/${slotId}`,
    { method: "DELETE" },
    token,
  );
}

export interface ThreadMessage {
  id: string;
  thread_id: string;
  sender_id: string;
  body: string;
  sent_at: string;
}

export interface ThreadMessageListResponse {
  items: ThreadMessage[];
  total: number;
}

export function fetchThreadMessages(
  token: string,
  threadId: string,
): Promise<ThreadMessageListResponse> {
  return request<ThreadMessageListResponse>(`/threads/${threadId}/messages`, {}, token);
}

export function postThreadMessage(
  token: string,
  threadId: string,
  body: string,
): Promise<ThreadMessage> {
  return request<ThreadMessage>(
    `/threads/${threadId}/messages`,
    { method: "POST", body: JSON.stringify({ body }) },
    token,
  );
}
