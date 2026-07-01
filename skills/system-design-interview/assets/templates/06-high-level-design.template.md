# High-Level Design — [Problem Name]

## Architecture Evolution (Start Cheap)

| Version | Scale trigger | Architecture | Why it works / breaks |
|---------|---------------|--------------|------------------------|
| v0 | Current (1×) | Monolith + single DB | Handles ___ QPS because ... |
| v1 | | + cache / queue | Triggered when ... |
| v2 | 10× | | |

**Selected design:** v___ for current scale. Components beyond v0 are justified by [specific number].

## Contested Decision: [Topic]

| | Option A | Option B | Option C |
|---|----------|----------|----------|
| Forces | | | |
| **Selected** | | ✓ | |

**Solves:** ... **Worsens:** ... **When to change:** ...

## System Overview

```
[ASCII diagram — read path vs write path, protocols on arrows, QPS on stores]
```

## Flow 1: Write / Data Path

1. Client → ... (protocol, latency contribution)
2. ...
→ Durable at: [store]

## Flow 2: Read / Query Path

| Hop | Component | Protocol | Latency budget |
|-----|-----------|----------|----------------|
| 1 | | | ms |
| | **Total** | | **= P99 target** |

## Flow 3: Failure and Degradation

### Failure: [Component A] down

- **User impact:**
- **Degradation:**
- **Recovery:**
- **Stampede avoidance:**

### Failure: [Component B] down

(same structure)

## Flow 4: Deploy and Migration

- **Strategy:** canary / rolling / blue-green
- **Schema migration:**
- **Rollback:**

## Component Registry

| Component | Capacity (from Phase 1) | Failure mode | Owner |
|-----------|-------------------------|--------------|-------|
| | QPS / storage | If down → ... | Team |

## Technology Trade-off Triads

### [Component / decision]

- **Solves:**
- **Worsens:**
- **When to change:**

(repeat for each major addition beyond start-cheap design)

## Production References

- [System]: how it relates, where we diverge, lesson learned
