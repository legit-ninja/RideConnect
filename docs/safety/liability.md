# Liability and legal

## Context

Horses and riding carry inherent injury risk. Marketplace operators typically need waivers, clear terms of service, and often insurance-related disclosures. **This document is not legal advice** — items below require review by qualified counsel before launch.

## Legal gate (launch blocker)

The following are **prerequisites to public launch**, not parallel workstreams. A
"Legal gate" milestone sits between the closed pilot and public launch in the
roadmap; public signup does not open until every item below is closed:

1. Counsel review of NC equine activity liability statute and its notice/signage
   requirements as applied to a marketplace facilitator.
2. Lawyer-reviewed rider and owner waiver templates, wired into the pre-booking
   acknowledgment flow (including guardian co-sign for minors).
3. Terms of service and privacy policy (including data retention for verification
   records and audit logs).
4. Confirmation that Stripe Connect marketplace terms cover the commission model
   as planned (relevant even during the zero-fee launch — the flip to paid must be
   pre-cleared).

**Free launch note:** the zero-fee launch period (see `free-launch-strategy.md`)
does not relax any item above. Free rides carry the same injury risk and the same
waiver, guardian, and ToS requirements. Zero revenue does not mean zero liability.

## Decisions (pending legal review)

| Topic | Working direction |
|-------|-------------------|
| User waivers | Riders and owners accept platform terms and activity-specific waivers before first booking (paid, friend, or free-launch) |
| Owner insurance | Consider requiring proof of liability insurance before listing (policy TBD with lawyer) |
| Minors | Guardian linkage and additional consent flows; guardian co-signature on waivers |
| Platform role | Marketplace facilitator, not employer of owners or operator of stables |
| Public listing pages | Approximate location only on public surfaces (see anti-trafficking.md); exact address disclosed only to confirmed parties — reduces premises-targeting risk |

## MVP minimum (assumptions)

- Terms of service and privacy policy published before public signup.
- In-app acknowledgment of risk before booking confirmation.
- Admin ability to remove listings and users violating safety policies.

## Open questions (requires legal review)

- State-specific equine activity liability statutes (especially NC and adjacent launch states — re-review at each expansion phase).
- Whether Stripe Connect marketplace terms cover our commission model as planned.
- Insurance products for owners or riders (platform-sponsored or third-party).
- Data retention for verification records and audit logs.
- Whether review content (user-generated) changes our moderation obligations.

## Related documents

- [Personas](../market/personas.md)
- [Anti-trafficking](anti-trafficking.md)
- [Free launch strategy](../strategy/free-launch-strategy.md)
