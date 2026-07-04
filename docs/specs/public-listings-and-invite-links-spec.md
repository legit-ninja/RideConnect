# Spec — Public Shareable Listings & Invite Links

**Status:** Draft for implementation
**Owner:** Jeremy
**Related docs:** `data-model-additions.md`, `anti-trafficking.md`, `liability.md`, `free-launch-strategy.md`

## Purpose

RideConnect's growth wedge is the existing horse community — county Facebook groups,
barn group chats, tack-swap pages. We do not replace those spaces; we become the
trust-and-transaction layer underneath them. Two features make that concrete:

1. **Public shareable listing pages** — every listing gets a public URL that renders
   as a rich card (Open Graph) when posted in Facebook groups or texted to a friend,
   with contact/booking gated behind signup + verification.
2. **Invite links** — an owner can generate a tokenized Verified Friend invite link
   and drop it in a group chat, without knowing the recipient's account (or whether
   they have one yet).

Both features are inbound funnels **onto** the platform. Nothing here creates an
off-platform escape hatch (see Safety Boundaries).

---

## Part 1 — Public Listing Pages

### Routes

| Route | Auth | Purpose |
|---|---|---|
| `GET /l/{slug}` (frontend) | Public | Public listing page, SSR with OG metadata |
| `GET /api/public/listings/{slug}` | Public | JSON for the public page (filtered fields only) |
| `GET /api/listings/{id}` | Authenticated + verified | Full listing detail (existing) |

- `slug` is a URL-safe, non-enumerable identifier: `{kebab-animal-name}-{6-char-base32}`
  e.g. `duke-7f3k2q`. Never expose the sequential/UUID primary key in public URLs.
- Slugs are stable for the life of the listing. Deactivated listings return a
  friendly "no longer available" page (HTTP 200 with noindex), not a 404, so old
  Facebook posts degrade gracefully.

### What the public page shows (and hides)

**Visible to anyone (logged out):**
- Animal first name, species, breed, age, photos
- Activity types offered (lesson / trail / lease / day rental) and price (or "Free-launch: no booking fees" during free launch)
- **Approximate location only**: `display_location` string (e.g. "Watauga County, NC" or "≈20 min from Boone") + optional map circle with ≥ 5 km radius jitter, centered on an offset point — never the true coordinates
- Owner **first name + last initial**, "✓ Verified Owner" badge, member-since month/year
- Aggregate review stats once reviews exist (count + average)
- Primary CTA: **"Sign up to request a ride"** → signup → verification → booking flow

**Never on the public page:**
- Exact address, true lat/lng, directions, or property photos that identify the parcel (house numbers, road signs, distinctive gates)
- Owner's full name, phone, email, or social links
- Any free-text field where an owner could paste contact info without review — the
  public page renders only structured fields; the long-form `description` is shown
  **only to authenticated, verified users** (MVP-simple way to keep "text me at…"
  off the public surface without building content moderation yet)
- Calendar/availability detail (show "Availability: weekly" tier at most; exact
  slots are post-auth)

**Exact address disclosure:** revealed only after a booking reaches `approved`
status (or an accepted friend connection exists), consistent with
`anti-trafficking.md` — location transparency is for confirmed parties, not the
public internet.

### Open Graph / sharing metadata

SSR these tags on `/l/{slug}` (Next.js `generateMetadata`):

```
og:title        "{Animal name} — {activity types} in {display_location} | RideConnect"
og:description  "Ride with a verified owner. Every RideConnect member is ID-verified. {price line}"
og:image        1200×630 generated share card (see below)
og:type         website
og:url          canonical https://rideconnect.app/l/{slug}
twitter:card    summary_large_image
```

**Share card image** (`/api/og/{slug}`, generated with `@vercel/og` or Pillow on the
FastAPI side): primary listing photo, animal name, activity chips, display_location,
and the Verified Owner badge rendered onto the image itself. The badge-on-image
matters — it's the trust signal that survives the screenshot.

Add `robots` noindex on deactivated listings; active listings are indexable
(free SEO for "trail rides near Boone NC" is a channel).

### Share affordances (owner side)

On the owner's listing management view:
- "Copy share link" button
- "Share to Facebook" (plain `https://www.facebook.com/sharer/sharer.php?u=` — no
  Graph API integration; group posting is a human act, per GTM strategy)
- Preview of the rendered share card so owners trust what will appear

### Funnel instrumentation

Append `?src=` params owners don't have to think about (`share_copy`, `share_fb`)
and log: public page view → signup start → verification complete → first booking
request, keyed to the originating listing. This is the core growth metric for the
whole social-wedge strategy.

---

## Part 2 — Invite Links (tokenized Verified Friend invites)

### Problem with current model

`FRIEND_INVITE` requires `rider_id` at creation — but the real flow is "owner texts
a link to the barn group chat," where recipients may not have accounts. The invite
must exist **before** the rider does.

### Flow

1. Owner (verified) taps **"Invite a friend to ride"** → chooses scope: a specific
   animal, or all their animals → gets a link: `https://rideconnect.app/i/{token}`
2. Owner shares link by text / group chat / email (their channel, not ours).
3. Recipient opens link → landing page: "**{Owner first name}** invited you to ride
   **{animal(s)}** for free on RideConnect. You'll need to verify your ID first —
   every member does."
4. Recipient signs up (or logs in) → completes KYC → token is **redeemed**, creating
   the concrete `FRIEND_INVITE` row binding `owner_id ↔ new rider_id`.
5. Owner gets a notification: "**{Rider full name}** accepted your invite" with an
   **approve/decline** step. A group-chat link can be forwarded; the owner must
   confirm the person who redeemed it is who they meant. Only after owner
   confirmation does the friend connection go active.

### Token rules

- Single-use by default. Multi-use tokens (up to N redemptions, N ≤ 10) are allowed
  for the group-chat case but each redemption still requires individual owner
  confirmation.
- Expiry: 14 days default, owner-configurable up to 30.
- Rate limits (also feeds pattern-flag system, see Safety Boundaries):
  - Max 10 active tokens per owner
  - Max 25 redemptions per owner per 30 days → exceeding queues account for admin review rather than hard-blocking
- Revocable by owner at any time; revocation invalidates unredeemed tokens only.

### Minors

- If the redeeming user is a minor: redemption **pauses** until a verified guardian
  account is linked and the guardian approves the specific connection. The owner
  confirmation step shows "Minor rider — guardian approved ✓" state.
- Per `anti-trafficking.md` pattern flags: an owner whose redemptions skew heavily
  toward minors gets auto-queued for admin review. The token model gives this flag
  a clean, countable signal.

### Routes

| Route | Auth | Purpose |
|---|---|---|
| `POST /api/invites/tokens` | Owner, verified | Create token (scope, max_uses, expiry) |
| `DELETE /api/invites/tokens/{id}` | Owner (creator) | Revoke |
| `GET /i/{token}` (frontend) | Public | Invite landing page (owner first name, animal preview — same field filtering as public listings) |
| `POST /api/invites/tokens/{token}/redeem` | Authenticated + verified | Redeem → creates pending FRIEND_INVITE |
| `POST /api/invites/{invite_id}/confirm` | Owner | Owner confirms/declines the redeemed identity |

Schema for `INVITE_TOKEN` and the `FRIEND_INVITE` changes: see
`data-model-additions.md`.

---

## Part 3 — Safety Boundaries (normative)

These are requirements, not suggestions. They reconcile this feature set with
`anti-trafficking.md`:

1. **Inbound only.** Public pages and invite links pull people onto the platform.
   No feature here may surface direct contact details (phone, email, exact address,
   social handles) to unverified or unconnected parties.
2. **Approximate location on all public surfaces.** True coordinates/address are
   revealed only post-approval (booking) or post-confirmation (friend connection).
   Enforce at the API serializer level (separate `PublicListing` response model),
   not just in frontend rendering.
3. **Owner-confirmed identity on invite redemption.** A forwarded link never creates
   an active connection by itself.
4. **All resulting messaging stays on-platform**, on booking or friend-connection
   threads (see THREAD model in `data-model-additions.md`).
5. **Public rider profiles (future)** exist to bring arrangements onto RideConnect
   ("book me through RideConnect"), not to credential off-platform arrangements. Any
   public profile ships with the same field-filtering discipline as public listings.
6. **Free-text on public surfaces is deferred** until content moderation exists.
   Structured fields only.

---

## Part 4 — Implementation order

1. Schema migrations (`data-model-additions.md`) — THREAD, REVIEW, LISTING_PHOTO,
   slug, INVITE_TOKEN, display_location
2. `PublicListing` serializer + `GET /api/public/listings/{slug}`
3. Next.js `/l/[slug]` SSR page + `generateMetadata` OG tags
4. OG share-card image generation
5. Owner share affordances + funnel event logging
6. Invite token create/landing/redeem/confirm flow
7. Guardian-pause path for minor redemptions
8. Rate limits + admin-review queue hooks

Items 1–5 are shippable value on their own; 6–8 complete the invite system.

---

## Manual verification checklist

1. Run `pytest` — especially `tests/test_public_listing_security.py`.
2. Create a listing as a verified owner → open `/l/{slug}` logged out.
3. View page source: true `address`, `animal.lat`, and `animal.lng` must be absent.
4. Confirm `/api/og/{slug}` renders a share card.
5. Create an invite token → redeem with a second verified account → owner confirms → thread row exists.
6. Mark an approved booking complete → both parties submit reviews → aggregates appear on the public listing.
7. Repo grep: `address` / true coordinates must not appear in `PublicListing` or other public serializers.
