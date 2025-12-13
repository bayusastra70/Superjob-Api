# Quick Action Dashboard Metrics & New Item Badge API Spec

## Overview
- Purpose: provide recruitment metrics and “new” badges for employer dashboard.
- Auth: JWT (Bearer) required. Employer can only access own data (enforce employer_id from token vs path).
- Path base: `/employers/{employer_id}/dashboard/metrics`.
- Default lookback: 72h for “new” counts (configurable via query).

## Endpoints
### GET `/employers/{employer_id}/dashboard/metrics`
- Description: returns aggregate metrics + badge flags.
- Query params:
  - `lookback_hours` (int, optional, default 72, min 1, max 168) — window for “newApplicants” and “newJobPosts”.
  - `include_seen_state` (bool, optional, default false) — if true, returns `seen_at` timestamps for new items.
- Headers: `Authorization: Bearer <JWT>`
- Responses:
  - 200 OK
    ```json
    {
      "employer_id": "uuid",
      "metrics": {
        "activeJobPosts": 12,
        "totalApplicants": 320,
        "newApplicants": 7,
        "newMessages": 3,
        "newJobPosts": 2
      },
      "badges": {
        "newApplicants": true,
        "newMessages": true,
        "newJobPosts": true
      },
      "windowHours": 72,
      "seen": {
        "newApplicants": "2025-12-08T05:00:00Z",
        "newMessages": "2025-12-08T05:00:00Z",
        "newJobPosts": "2025-12-08T05:00:00Z"
      }
    }
    ```
  - 400 Bad Request (e.g., invalid lookback)
    ```json
    { "detail": "lookback_hours must be between 1 and 168" }
    ```
  - 401 Unauthorized (missing/invalid JWT)
  - 403 Forbidden (employer_id mismatch with JWT)
  - 404 Not Found (employer not found)
  - 500 Internal Server Error

### POST `/employers/{employer_id}/dashboard/metrics/mark-seen`
- Description: FE calls after badge is shown/acknowledged to clear “new” badges.
- Body:
  ```json
  {
    "items": ["newApplicants", "newMessages", "newJobPosts"]
  }
  ```
  - `items` required, non-empty, values from enum above.
- Headers: `Authorization: Bearer <JWT>`
- Responses:
  - 204 No Content (idempotent)
  - 400 / 401 / 403 / 404 / 500 as above

## Badge Rules (evaluated on GET)
- `newApplicants`: count applicants with status “applied” created_at >= now - lookback_hours OR not seen. Badge if count > 0.
- `newMessages`: count unread inbound messages. Badge if count > 0.
- `newJobPosts`: job postings status “published” or “active” created_at >= now - lookback_hours OR not seen. Badge if count > 0.
- `activeJobPosts`: all job postings status active/published (no badge).
- `totalApplicants`: total applicants for employer (no badge).
- Mark-seen: store per-employer timestamps for each badge key; on GET, items newer than `seen_at` still count as “new”.

## Validation Rules
- `employer_id` path must match JWT claims.
- `lookback_hours` integer 1–168.
- `items` in POST must be subset of allowed enum; reject empty list.

## OpenAPI/Swagger Notes
- Tag: `dashboard-metrics`.
- Schemas to expose:
  - `DashboardMetrics` (metrics object)
  - `DashboardBadges` (booleans)
  - `DashboardMetricsResponse`
  - `MarkSeenRequest`
- Ensure docs visible at `/docs` (FastAPI default) or `/api-docs` if configured.

## Error Structure
- Use FastAPI default: `{ "detail": "<message or object>" }`.
- For validation errors, rely on Pydantic/HTTP 422.

## Data Flow (simplified)
- GET:
  1. Auth & employer check.
  2. Read last seen timestamps (per badge key) for employer.
  3. Compute counts with `lookback_hours` and `seen_at` thresholds.
  4. Derive badge booleans (count > 0).
  5. Return metrics + badges + windowHours (+ seen if requested).
- POST mark-seen:
  1. Auth & employer check.
  2. Upsert current timestamp for requested items.
  3. Return 204.

## Future (pagination-ready)
- If later returning lists of new applicants/messages/job posts, add optional `include_items=true` and paginated arrays (`items`, `nextCursor`). Until then, keep aggregate-only for speed.
