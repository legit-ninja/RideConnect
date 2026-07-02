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
  is_admin: boolean;
  verification_status: VerificationStatus;
  is_minor: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export type ActivityType = "lesson" | "lease" | "trail_ride" | "day_rental";

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
  lat: number;
  lng: number;
  address: string;
  photo_urls: string[];
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

export function registerUser(payload: {
  email: string;
  password: string;
  is_rider: boolean;
  is_owner: boolean;
}): Promise<User> {
  return request<User>("/auth/register", {
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

export function fetchSpecies(): Promise<Species[]> {
  return request<Species[]>("/species");
}

export function fetchListings(params: {
  activity_type?: ActivityType;
  species_id?: string;
  min_price?: number;
  max_price?: number;
} = {}): Promise<ListingSummary[]> {
  const search = new URLSearchParams();
  if (params.activity_type) search.set("activity_type", params.activity_type);
  if (params.species_id) search.set("species_id", params.species_id);
  if (params.min_price !== undefined) search.set("min_price", String(params.min_price));
  if (params.max_price !== undefined) search.set("max_price", String(params.max_price));
  const query = search.toString();
  const path = query ? `/listings?${query}` : "/listings";
  return request<ListingSummary[]>(path);
}

export function fetchListing(id: string): Promise<ListingDetail> {
  return request<ListingDetail>(`/listings/${id}`);
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

export type FriendInviteStatus = "pending" | "accepted" | "declined" | "cancelled";

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
  | "cancelled";

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
  note: string | null;
  requested_at: string;
  listing_price: string;
  activity_type: string;
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
    { method: "PATCH", body: JSON.stringify({ status: "cancelled" }) },
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
  payload: { listing_id: string; scheduled_at?: string; note?: string },
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
  status: "approved" | "declined" | "cancelled",
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
