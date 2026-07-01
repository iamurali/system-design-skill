# Non-Functional Requirements — [Problem Name]

## Capacity Estimation

Derived from **Scale Assumptions** in `01-requirements.md`. Show all math inline.

### Estimation Chain

```
DAU = ___ (from Phase 1)
Read QPS  = DAU × reads/user/day ÷ 86,400 = ___ avg → ___ peak
Write QPS = DAU × writes/user/day ÷ 86,400 = ___ avg → ___ peak
Storage/day = writes/day × object_size = ___
Total storage = storage/day × retention = ___
Read bandwidth  = peak_read_QPS × response_size = ___
Write bandwidth = peak_write_QPS × request_size = ___
Server count = peak_QPS ÷ per_server_QPS (from numbers-to-know.md) = ___
```

### Component Load Summary

| Component | Peak load | Notes |
|-----------|-----------|-------|
| | | |

### Growth Trajectory

| Tier | DAU / QPS | What breaks first |
|------|-----------|-------------------|
| 1× (launch) | | |
| 10× | | |
| 100× | | |

## Latency Targets

| Percentile | Target | Path |
|------------|--------|------|
| P50 | ms | |
| P95 | ms | |
| P99 | ms | |
| P99.9 | ms | (if applicable) |

### Latency Budget Breakdown (must sum to P99 ±10%)

| Hop | Budget | Notes |
|-----|--------|-------|
| | ms | |
| | ms | |
| **Total P99** | **ms** | |

## Availability and Error Budget

| Component / API | Target | Error budget (concrete) |
|-----------------|--------|-------------------------|
| | 99.9% | ~43 min downtime/month |
| | | |

**Budget consumers:** deploys, dependency failures, hot partitions.

## Consistency Model

| Data / Operation | Model | User-facing consequence |
|------------------|-------|-------------------------|
| | Eventual / Strong / ... | User may/might see ... for up to X |

## Durability

| Data class | RPO | RTO | Mechanism |
|------------|-----|-----|-----------|
| | | | |

## Security NFRs

- Authentication / authorization:
- Encryption in transit / at rest:
- Abuse / rate limiting:

## Operational Requirements

| Requirement | Target |
|-------------|--------|
| Zero-downtime deploy | |
| Monitoring / alerting thresholds | |
| Capacity planning cadence | |

### Runbook: [Top Failure Scenario]

1. **Detect:** alert / symptom
2. **Mitigate:** immediate action
3. **Recover:** restoration steps
4. **Post-incident:** prevent recurrence
