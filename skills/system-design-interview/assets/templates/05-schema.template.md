# Schema — [Problem Name]

## Storage Overview

| Store role | Technology class | Serves AP- | Notes |
|------------|------------------|------------|-------|
| Primary | SQL / KV / … | | |
| Derived / cache | | | |

## Primary Schema

### [Table / Collection Name]

| Column / field | Type | Purpose |
|----------------|------|---------|
| PK | | |
| | | |

**Indexes:**

| Index | Columns | Serves | Write amp at peak W QPS |
|-------|---------|--------|-------------------------|
| | | AP- | |

## Partitioning / Sharding

| Shard key | Rationale | Hot spot risk | Mitigation |
|-----------|-----------|---------------|------------|
| | Traces to Phase 1 write QPS | | |

## Derived / Auxiliary Structures

(Cache keys, log topics, search indexes — only if shape requires)

```
Key pattern: ...
TTL: ...
Update path: ...
```

## Schema ↔ API Alignment

| API endpoint | Query / access | Index or PK used |
|--------------|----------------|------------------|
| | | |

## Denormalization (if any)

| Duplicated data | Justification (read:write, join cost) |
|-----------------|---------------------------------------|
| | |
