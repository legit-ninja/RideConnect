# Marketplace UI

Trust-first marketplace for riders and owners — browse, book, and host verified riding experiences.

## Dev logins

After `make seed`, all email users use password `password123`:

| Email | Roles | Verification | Use for |
|-------|-------|--------------|---------|
| `rider.verified@example.com` | rider | verified | Browse, request paid rides |
| `owner.verified@example.com` | owner | verified | Approve bookings, friend invites |
| `both.verified@example.com` | rider + owner | verified | Typical dual-role user |
| `owner.verified2@example.com` | owner | verified | Stable operator (many listings) |
| `rider.unverified@example.com` | rider | unverified | Blocked booking flow |
| `owner.pending@example.com` | owner | pending | Blocked hosting |
| `minor.rider@example.com` | rider (minor) | unverified | Guardian warning |
| `guardian@example.com` | rider + owner | verified | Linked guardian for minor |
| `oauth.only@example.com` | — | unverified | OAuth only (no password) |

**Admin login** (from `.env`, not seed — password is **not** `password123`):

| Email | Password | Roles | After login |
|-------|----------|-------|-------------|
| `admin@example.com` | `change-me-admin` (see `.env` `ADMIN_PASSWORD`) | admin + rider + owner | `/admin` |

**Seeded scenarios** (after migrations + `make seed`):

- Accepted friend invite: `owner.verified` → `rider.verified`
- Pending invite (blocked until verified): `owner.verified` → `rider.unverified`
- Sample bookings: pending paid, approved, and declined examples on seeded listings

**Bulk accounts** (`bulk.rider.*`, `bulk.owner.*`, `bulk.both.*`) are for admin UI preview only (pagination, owner animal counts). Use the persona emails above for marketplace walkthroughs.

## Routes

| Route | Purpose |
|-------|---------|
| `/` | Landing |
| `/login`, `/register` | Auth |
| `/dashboard` | Role-aware hub — next steps by persona |
| `/listings` | Browse rides (filters, cards) |
| `/listings/[id]` | Listing detail + request ride |
| `/rider/bookings` | Rider booking requests |
| `/owner/animals` | Owner animal list |
| `/owner/animals/new`, `/owner/animals/[id]` | Animal CRUD |
| `/owner/listings` | Owner listing list |
| `/owner/listings/new`, `/owner/listings/[id]` | Listing CRUD |
| `/owner/friends` | Verified friend invites |
| `/owner/bookings` | Owner booking inbox (approve/decline) |

## Verification gates

- **Auth ≠ verification** — OAuth sign-in does not satisfy KYC.
- Unverified users cannot create listings, send booking requests, or send friend invites.
- Minors require a verified linked guardian before ride activity.
- UI shows explicit blocked states with next steps — not silent empty tables.

## Booking flow (preview)

1. Verified rider browses `/listings` and opens a listing.
2. **Request ride** submits a booking request (paid listings → `pending_payment` stub; friend-only → requires accepted friend invite).
3. Owner reviews requests at `/owner/bookings` and approves or declines.
4. All payments stay on-platform (Stripe deferred; no off-platform copy).

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
