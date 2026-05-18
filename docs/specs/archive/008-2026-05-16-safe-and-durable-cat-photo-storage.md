# Safe and Durable Cat Photo Storage

Priority: P1

Problem:
Photo upload accepts any `data:image/*` prefix, decodes unbounded base64, writes the bytes as `{cat_id}.jpg`, and stores a relative file path in `app/routers/cats.py:67-93`. Deletion trusts the stored path in `app/routers/cats.py:102-105`. Docker Compose persists only Postgres data, not uploads.

Current behavior:

- Server-side file type and image validity are not verified.
- Upload size is not constrained.
- Runtime uploads may be lost when containers are rebuilt.
- Stored path handling is more permissive than needed.

Proposed behavior:

- Enforce maximum encoded and decoded upload sizes.
- Verify actual image content server-side and normalize to a safe format.
- Store only controlled relative filenames or object keys, never arbitrary paths.
- Add a persistent uploads volume or move photos to external object storage.
- Serve uploaded files with safe content headers.

Acceptance criteria:

- Non-image payloads with an image data URL prefix are rejected.
- Oversized payloads are rejected before excessive memory use.
- Uploaded photos survive container rebuilds.
- Deleting a photo cannot remove files outside the configured photo directory.

Verification:

- Add API tests for valid upload, invalid base64, wrong MIME, oversized image, and delete safety.
- Add Compose verification that `uploads` is mounted persistently.
