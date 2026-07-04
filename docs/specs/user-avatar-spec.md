# Spec — User Profile Photo (Avatar)

**Status:** Implemented (backend)
**Related docs:** `data-model-additions.md`

## Data model

`User.profile_photo_storage_key` (nullable `string(512)`) — same storage-key pattern
as `LISTING_PHOTO.storage_key`, so avatars reuse the existing upload pipeline
(`app/services/storage.py`: `put_object` / `get_public_url`) instead of a new one.
No `avatar_url` column — the URL is computed at read time from the storage key so
the storage backend can change without a migration.

Migration: `011_user_profile_photo`.

## API

- `POST /auth/me/avatar` — multipart `file` upload. Requires a **verified** user
  (`require_verified`); identity is taken from the bearer token, so a user can only
  ever set their own avatar. Image is EXIF-stripped and downscaled (max 512px) before
  storage, same as listing photos, then re-encoded as JPEG.
- `GET /auth/me`, `POST /auth/register` — both return `UserResponse.avatar_url`, a
  computed public URL (or `null`).
- Registration never requires a photo; `profile_photo_storage_key` stays `null` until
  the user optionally uploads one.

## Public surfaces

Avatars are **never** exposed on public/anonymous surfaces. `PublicListing` (public
listing cards, search results) only exposes `owner_first_name` + `owner_last_initial`
— no avatar, no email, no photo. Do not add `avatar_url` to `PublicListing` or any
other public serializer.

## Default rendering (frontend contract)

When `avatar_url` is `null`, the client renders **initials** (first + last initial)
on a generated background, not a broken image and not a Gravatar-style
email-hash lookup. RideConnect never derives an avatar from email (Gravatar or
similar) — that would leak a hash of PII to a third party for every user, verified
or not.
