# Marketplace UI

Trust-first marketplace for riders and owners — browse, book, and host verified riding experiences.

## Base44 PR #2 — do not merge

[PR #2 (luxury UI redesign)](https://github.com/legit-ninja/RideConnect/pull/2) adds a parallel `src/` + Tailwind stack that is **not integrated** with this app. Do not merge it into `master`.

| PR dependency | Native alternative |
|---------------|-------------------|
| Base44 SDK (`base44Client`) | [`frontend/lib/api.ts`](../frontend/lib/api.ts) + FastAPI |
| Tailwind + shadcn (`@/components/ui/*`) | CSS modules + [`globals.css`](../frontend/app/globals.css) tokens |
| React Router | Next.js App Router |
| TanStack Query | Server components + client `fetch` / `useEffect` |
| framer-motion | CSS utilities in [`utilities.css`](../frontend/app/utilities.css) |
| Google Fonts CDN | `next/font/google` (Playfair Display headings, Inter body fallback) |
| Unsplash / Base44 CDN images | Local assets under `frontend/public/images/` (hero galloping horse, seed photos) |

The luxury visual design is ported natively into `frontend/` (gold primary, Playfair headings, hero home page, site footer, enhanced cards).

## Dev logins

After `make seed`, all email users use password `password123`:

| Email | Roles | Verification | Use for |
|-------|-------|--------------|---------|
| `rider.verified@example.com` | rider (Beginner skill) | verified | Browse, request paid rides; skill-mismatch booking as rider |
| `owner.verified@example.com` | owner, riding instructor | verified | Approve bookings, friend invites; instructor (not admin-verified) |
| `both.verified@example.com` | rider + owner (Intermediate skill) | verified | Dual-role user; confirmed skill via owner reviews |
| `owner.verified2@example.com` | owner, verified trainer | verified | Advanced listings, skill-warning inbox, admin flag target |
| `rider.unverified@example.com` | rider | unverified | Blocked booking flow |
| `owner.pending@example.com` | owner | pending | Blocked hosting |
| `minor.rider@example.com` | rider (minor) | unverified | Guardian warning |
| `minor.rider2@example.com` … `minor.rider4@example.com` | rider (minor) | verified | Trainer minor-skew flag fixtures |
| `guardian@example.com` | rider + owner | verified | Linked guardian for minors |
| `family.verified@example.com` | rider (family account) | verified | 3-member roster incl. one minor; family booking walkthrough |
| `oauth.only@example.com` | — | unverified | OAuth only (no password) |

**Admin login** (from `.env`, not seed — password is **not** `password123`):

| Email | Password | Roles | After login |
|-------|----------|-------|-------------|
| `admin@example.com` | `change-me-admin` (see `.env` `ADMIN_PASSWORD`) | admin + rider + owner | `/admin` |

**Seeded scenarios** (after migrations + `make seed`):

- Accepted friend invite: `owner.verified` → `rider.verified`
- Pending invite (blocked until verified): `owner.verified` → `rider.unverified`
- Sample bookings: pending paid, approved, declined, and **skill-mismatch pending** (`rider.verified` → Comet day rental, min Advanced Intermediate)
- Completed bookings with owner-observed reviews for `both.verified` (enables **Confirmed Intermediate** on counterparty profile)
- Open availability slots on select listings for the next 14 days (calendar discovery)
- **Public listing community fields**: browse Comet or Shadow listings for min skill, weight limit, tack expectations, and verified-trainer badge (`owner.verified2`)
- **Location privacy**: Star’s listing uses a street address in seed data; public page shows city-only label
- **Admin flags**: `/admin/flags` includes `minor_invite_skew` for `owner.verified2@example.com` (trainer with disproportionate minor friend connections)
- **Family booking**: pending group request from `family.verified@example.com` (Rivera Family, 3 riders) on Star's trail listing — visible as one grouped row at `/owner/bookings`

**Walkthrough hints:**

| Goal | Login | Where |
|------|-------|-------|
| Owner inbox skill warning | `owner.verified2@example.com` | `/owner/bookings` — pending Comet rental request |
| Family roster + grouped booking | `family.verified@example.com` | `/settings` (roster editor); `/listings` → book with multi-select |
| Owner family inbox | `owner.verified@example.com` | `/owner/bookings` — **Family — Rivera Family** (3 riders) |
| Public gear/skill requirements | (no login) | Public listing slug for Comet or Shadow |
| Counterparty confirmed skill | `owner.verified@example.com` or `owner.verified2@example.com` | `GET /users/{both_verified_id}/counterparty` or connected booking UI |
| Trainer verification toggle | `admin@example.com` | `/admin/users` → user detail |

**Bulk accounts** (`bulk.rider.*`, `bulk.owner.*`, `bulk.both.*`) include varied rider skill levels, trainer self-reports, and listing community fields for admin/search UI density. Use the persona emails above for focused marketplace walkthroughs.

## Routes

| Route | Purpose |
|-------|---------|
| `/` | Luxury landing (hero, how-it-works, featured listings) |
| `/login`, `/register` | Auth |
| `/dashboard` | Role-aware hub — next steps by persona |
| `/calendar` | Verified users: personal schedule, open ride slots, daily weather |
| `/listings` | Browse rides (activity, species, price, riding style filters; cards show style chips) |
| `/listings/[id]` | Listing detail + request ride |
| `/rider/bookings` | Rider booking requests |
| `/owner/animals` | Owner animal list |
| `/owner/animals/new`, `/owner/animals/[id]` | Animal CRUD (horses require ≥1 riding style: Western, English, Therapy) |
| `/owner/listings` | Owner listing list |
| `/owner/listings/new`, `/owner/listings/[id]` | Listing CRUD + availability slot management |
| `/owner/friends` | Verified friend invites |
| `/owner/bookings` | Owner booking inbox (list + calendar views, approve/decline; family groups shown as one row) |
| `/settings` | Profile setup — individual vs family rider type, family roster editor |

## Verification gates

- **Auth ≠ verification** — OAuth sign-in does not satisfy KYC.
- Unverified users cannot create listings, send booking requests, or send friend invites.
- Minors require a verified linked guardian before ride activity.
- UI shows explicit blocked states with next steps — not silent empty tables.

## Booking flow (preview)

1. Verified rider browses `/listings` and opens a listing.
2. **Request ride** submits a booking request (paid listings → `pending_payment` stub; friend-only → requires accepted friend invite).
3. **Family accounts** select one or more roster members at booking time; the API creates linked booking rows under one `family_booking_group_id`.
4. Owner reviews requests at `/owner/bookings` and approves or declines (family groups act as a single unit).
5. All payments stay on-platform (Stripe deferred; no off-platform copy).

## Family rider registration

1. Verified adult rider opens `/settings` and switches **Individual** → **Family**.
2. Enter family name, size (2–20), and roster rows (display name, skill level, minor flag).
3. Save via `PUT /auth/me/family-profile`; minors on the roster use the account holder as implicit guardian.
4. When booking, multi-select roster members; owner inbox shows **Family — {name}** with participant list.

## Friend invites

1. Verified owner sends invite by email at `/owner/friends`.
2. Invitee must be verified to accept.
3. Accepted invite unlocks free-ride eligibility for friend-only listings between that owner and rider pair.

## Related docs

- [Design system](design-system.md)
- [Admin UI](admin-ui.md)
- [Data model](data-model.md)
- [OAuth design](oauth-design.md)
- Product rules: `.cursor/rules/rideconnect-mvp.mdc`
