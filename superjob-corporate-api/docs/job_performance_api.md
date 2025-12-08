# Job Performance / Popularity API

Endpoint: `GET /employers/{employer_id}/job-performance`

Fields (per item):
- `job_id` (UUID)
- `job_title` (string)
- `views_count` (int)
- `applicants_count` (int)
- `apply_rate` (float 0-1)
- `status` (active | draft | closed)
- `updated_at` (ISO datetime)

Query params:
- `sort_by`: views | applicants | apply_rate | status (default: views)
- `order`: asc | desc (default: desc)
- `status`: active | draft | closed (optional filter)
- `page`: int >=1 (default 1)
- `limit`: 1–100 (default 20)

Response (paginated):
```json
{
  "items": [
    {
      "job_id": "uuid",
      "job_title": "Product Designer",
      "views_count": 120,
      "applicants_count": 24,
      "apply_rate": 0.2,
      "status": "active",
      "updated_at": "2025-12-08T12:00:00Z"
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 3,
  "sort_by": "views",
  "order": "desc",
  "status_filter": null
}
```

Mock data:
- Included in the running app (router `job_performance`) for FE to integrate while backend aggregates are being built.

Validation/errors:
- 200 OK with data
- 422 on invalid sort/order/status/page/limit
- 401/403/404/500 as applicable (auth to be added when wiring real data).
