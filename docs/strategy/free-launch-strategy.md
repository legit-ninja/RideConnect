# Free Launch Strategy — Zero-Fee Period, Social Proof & Community Incentives

**Decision:** RideConnect launches with **no booking fees** for all participants.
Commission is deferred, not abandoned. The free period buys the two things a
two-sided marketplace can't fundraise its way past: liquidity and trust.

## Why free-first is the right call here (not just a budget constraint)

- The incumbent behavior (Facebook group posts, word of mouth) is free. Asking a
  tight-knit rural community to pay a commission for something they've always done
  informally, before the platform has proven value, is the fastest way to be seen
  as a middleman rather than a trust layer.
- The platform's real product at launch is **verification and auditability**, and
  its real currency is **reviews and ride history**. Every free booking still
  generates the assets (verified profiles, completed rides, reviews) that make
  monetization possible later.
- "Free at launch, everyone verified" is a much stronger group-chat pitch than any
  price point.

## Implementation: turn payments off with config, not schema changes

**Keep the entire booking/transaction model intact.** The switch is a platform
setting, not a migration:

- `PLATFORM_COMMISSION_RATE = 0.0` (env/config) — or defer Stripe activation
  entirely and allow `BOOKING_REQUEST.payment_type = free_launch` alongside
  `paid` and `free` (friend).
- Recommended: **defer Stripe Connect onboarding** for owners during free launch.
  Stripe Connect onboarding is real friction (SSN, bank account); imposing it when
  no money moves will cost signups. Add owner Stripe onboarding as a prompt when
  paid bookings turn on.
- Keep `TRANSACTION` rows out of the free-launch path entirely (a $0 transaction
  row is noise); the completed `BOOKING_REQUEST` is the audit record.
- KYC identity verification is **not** deferred. Free launch changes pricing, never
  the verification gate.

**Tell users the truth about the future.** ToS and marketing say "free during our
founding period" — not "free forever." Communities forgive a planned change they
were told about; they punish a bait-and-switch.

## Social proof mechanics (the asset the free period exists to build)

1. **Reviews** (see `data-model-additions.md`) — double-blind, booking-gated.
   These are the platform's compounding asset; ship with the first booking flow.
2. **Verified badge + ride count on public pages** — "✓ Verified · 23 rides
   hosted" on a share card is the trust signal that converts a skeptical Facebook
   group.
3. **Milestones worth sharing** — after a completed ride or a review, generate a
   share card ("Duke's 10th trail ride on RideConnect ⭐ 4.9") the owner can post.
   Owners posting their own milestones into their own groups is the marketing
   budget you don't have.

## Community incentives (cheap, status-based — not discounts)

- **Founding Owner / Founding Rider badge** — permanent, visible on profiles and
  share cards, for anyone verified during the free-launch window. Costs nothing;
  creates urgency and belonging.
- **Ambassador program for group admins** — the admins of the major NC horse
  Facebook groups get founding-ambassador status, early feature input, and a named
  thank-you on the site. Their pinned post is worth more than any ad spend.
  (Revisit a referral commission for them once payments turn on.)
- **Barn/stable pages (later)** — let a boarding facility claim a page listing its
  verified members; taps existing real-world community structure instead of
  inventing new structure.

## Monetization trigger (decide the threshold now, in writing)

Turn on commission when, in a given region, roughly:
- ≥ N active verified owners and ≥ M monthly completed bookings (set N/M with
  pilot data), and
- repeat-booking rate shows riders coming back (retention, not just trial).

Flip sequence: announce to founding members first with a grace period (e.g.
founding owners keep 0% for 6 more months, or a permanently reduced rate — the
founding badge then carries real value), then enable Stripe onboarding prompts,
then default new listings to paid-capable.

## What this changes in the current docs

- **Business plan §5 / deck slide 6**: add a line — "Launch period: zero platform
  fees to establish liquidity and trust; commission activates per-region at
  liquidity thresholds."
- **Roadmap (§9)**: insert "Monetization switch-on (per-region threshold)" as an
  explicit milestone between public launch and regional expansion.
- **Liability**: free rides are still rides — waivers, guardian flows, and the
  legal-gate milestone before public launch apply with full force. Zero revenue
  does not mean zero liability.
