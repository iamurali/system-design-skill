# API Design — [Problem Name]

## API Overview

| API surface | Auth | Peak QPS | Notes |
|-------------|------|----------|-------|
| Public | | | |
| Internal | | | |

## Endpoints

### [Operation Name]

```
METHOD /v1/path
Headers:
  Authorization: Bearer …
  X-Idempotency-Key: … (writes)

Request:
{
  ...
}

Response: 200 OK
{
  ...
}
```

| Property | Value |
|----------|-------|
| Idempotent | yes / no |
| Pagination | cursor / none |
| Rate limit | per user / global |

---

(repeat per endpoint)

## Pagination

```
GET /v1/resource?cursor={opaque}&limit=50

Response:
{
  "items": [...],
  "next_cursor": "…",
  "has_more": true
}
```

## Error Contract

| HTTP | Code | Retry? | Meaning |
|------|------|--------|---------|
| 400 | INVALID_ARGUMENT | no | |
| 409 | CONFLICT | no | |
| 429 | RATE_LIMITED | yes | Retry-After header |
| 503 | UNAVAILABLE | yes | Backoff |

## Access Pattern Coverage

| AP ID | Endpoint | Notes |
|-------|----------|-------|
| AP-1 | | |
