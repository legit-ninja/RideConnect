# Admin UI

Trust-first operations console for RideConnect moderators.

## Access

1. Set admin credentials in `.env`:
   ```
   ADMIN_EMAIL=admin@example.com
   ADMIN_PASSWORD=change-me-admin
   ```
2. Sign in at http://localhost:3000/login
3. Navigate to http://localhost:3000/admin

Seeded dev users (password `password123`) are available after `make seed`. Use `owner.pending@example.com` to test the verification queue. Use `owner.verified2@example.com` for a verified horse trainer + riding instructor (shows under **Trainer claims** on the dashboard and in the users list Roles column).

**Bulk preview accounts** (~50 extra users for admin list pagination):

| Pattern | Count | Notes |
|---------|-------|-------|
| `bulk.rider.{01-25}@example.com` | 25 | Rider-only; mixed verification |
| `bulk.owner.{01-15}@example.com` | 15 | Owner-only; most have registered animals |
| `bulk.both.{01-10}@example.com` | 10 | Dual-role |

After seed you should see **60+ users** on `/admin/users` (bulk + personas + bootstrap admin). Try `bulk.owner.03@example.com` for an owner with animals and listings; `bulk.rider.01@example.com` for a rider with none. Password: `password123`.

## Routes

| Route | Purpose |
|-------|---------|
| `/admin` | Operations dashboard — attention cards for verification queue, inactive listings, signups |
| `/admin/users` | Search and browse all accounts |
| `/admin/users/[id]` | User detail — verification, roles, guardian warning, marketplace counts |
| `/admin/users/[id]?review=1` | Review mode — focused verification workflow with optional admin note |
| `/admin/verification` | Verification queue — unverified and pending users |
| `/admin/listings` | Listings moderation — activate/deactivate listings |
| `/admin/listings?owner_id=[id]` | Listings filtered to a specific owner |
| `/admin/audit` | Read-only admin action history |
| `/admin/bookings` | Placeholder — booking oversight (coming soon) |
| `/admin/reports` | Placeholder — reports queue (coming soon) |

## Verification workflow

1. Open **Verification** from the sidebar (badge shows queue count).
2. Click **Review** on a user row.
3. On the user detail page, review identity context:
   - Sign-in method (OAuth does **not** satisfy KYC)
   - Minor/guardian status
   - Marketplace activity
4. Optionally add an admin note (stored in audit log only).
5. **Approve**, **Mark pending**, or **Reject** (reject requires confirmation).
6. Actions are logged in **Audit log**.

## Trust rules in UI

- **Auth ≠ verification** — OAuth sign-in never implies ride eligibility.
- No UI copy encourages off-platform payment or communication.
- Destructive actions (reject, deactivate listing) require confirmation and are audit-logged.

## Related docs

- [Design system](design-system.md)
- [OAuth design](oauth-design.md) — backend OAuth; frontend buttons deferred
- [Data model](data-model.md)
- Product rules: `.cursor/rules/rideconnect-mvp.mdc`
