# Non-Functional Requirements — [Problem Name]

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
