# Anti-trafficking and platform safety

## Decision

RideConnect must not be usable for human or animal trafficking or for arrangements that evade platform oversight. We prioritize individual and family horse owners and ranches over opaque commercial exploitation.

## Product rules

1. **No off-platform escape hatches** — Features must not let two accounts fully leave the platform to transact or communicate. No open/anonymous direct messages; messaging only on booking or friend-invite threads (see `THREAD` model). A friend-invite thread opens only after the invite is fully active (owner-confirmed, and guardian-approved where the rider is a minor).

2. **Verification gate** — Unverified users cannot create listings, send booking requests, send friend invites, create invite tokens, or redeem invite tokens.

3. **Auditable connections** — Bookings, friend connections, invite-token redemptions, and payments log timestamps and actor IDs. No silent or anonymous actions.

4. **Owner-confirmed invite redemption** — Invite links can be forwarded, so a redemption never activates a friend connection by itself. The owner must confirm the specific verified identity that redeemed the token before the connection (and its message thread) goes active.

5. **Reporting** — Report control on every profile, listing, and booking; admin review queue.

6. **Pattern flags (MVP, simple)** — Examples: new account immediately attempting off-platform contact; owner with unusually high volume of minor friend invites or invite-token redemptions skewing toward minors; owner exceeding invite-token rate limits (>10 active tokens, or >25 redemptions in 30 days → auto-queue for admin review).

## Public surfaces (listings, invite landing pages, future public profiles)

Public shareable pages are the platform's growth wedge into existing social
communities. They are **inbound funnels only** and follow these rules:

- **Approximate location only.** Public pages show `display_location` (county, or
  "≈X min from {town}") and, if a map is shown, a circle around a jittered point
  offset ≥5 km from the true location. The verified exact address is revealed only
  after a booking is approved or a friend connection is active. Publishing a rural
  property's exact address publicly is a theft and personal-safety risk and defeats
  the purpose of verified-address transparency, which exists for confirmed parties.
- **No direct contact details** (phone, email, exact address, social handles) on
  any public surface, for any party.
- **Identity minimization**: owner shown as first name + last initial + verified
  badge. Full names appear only to connected/booked counterparties.
- **Structured fields only** on public pages until content moderation exists.
  Owner free-text (`description`) renders only for authenticated, verified users,
  so contact details can't be smuggled onto the public surface.
- **EXIF stripped** from all uploaded photos (GPS metadata would leak true
  location).
- **Allowlist serialization**: public API endpoints serialize exclusively through a
  dedicated `PublicListing` response model. Never filter fields in the frontend.
- **Public rider profiles (future)** exist to bring arrangements onto RideConnect,
  not to credential off-platform arrangements. Same field-filtering discipline.

## UI and copy

- Do not encourage cash or off-platform payment.
- Do not display owner/rider contact details in ways that bypass in-app messaging before a verified booking context exists.
- Invite landing pages state plainly that ID verification is required for everyone ("You'll need to verify your ID first — every member does"), setting the trust norm at first contact.

## Open questions

- Specific rate limits and automated suspension thresholds beyond the invite-token limits above.
- Partnership with NCMEC or industry safety orgs (post-MVP).
- Photo/content moderation for listings (fields exist — `moderation_status` — policy and tooling TBD).

## Related documents

- [Vision](../strategy/vision.md)
- [Liability](liability.md)
- [Public Listings & Invite Links spec](../specs/public-listings-and-invite-links-spec.md)
- [Data model additions](../specs/data-model-additions.md)
- Engineering: `.cursor/rules/rideconnect-mvp.mdc`
