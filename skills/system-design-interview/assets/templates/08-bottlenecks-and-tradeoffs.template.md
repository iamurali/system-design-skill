# Bottlenecks and Tradeoffs — [Problem Name]

## Bottleneck Analysis

### Bottleneck 1: [Name]

**Root cause:**

**Mitigations:** (2–3)

**Real-world analogy:** [Company, ~year, lesson]

(repeat for 6+ bottlenecks)

## Failure Matrix

| Failure | Blast Radius | Detection | Degradation | Recovery | RTO |
|---------|--------------|-----------|-------------|----------|-----|
| Node crash | | | | | |
| Network partition | | | | | |
| Cascading failure | | | | | |
| Data corruption | | | | | |
| Deploy failure | | | | | |

## Real-World Incidents

1. **[Company] (~year):** root cause — lesson
2. ...
3. ...

## Anti-Patterns

### Anti-pattern 1: [Mistake]

- **Why it seems right:**
- **Why it fails in production:**
- **Correct approach:**

(repeat for 3+)

## Tradeoff Summary Matrix

| Decision | Chosen | Alternative | Why |
|----------|--------|-------------|-----|
| | | | |

## Evolution Roadmap

| Scale | Breaking point | Architectural change | Migration |
|-------|----------------|----------------------|-----------|
| 10× | At ___ QPS, ___ breaks because ... | | |
| 100× | | | |

## Coverage Sweep

| Building block | Used / Deferred | Reason if deferred |
|--------------|-----------------|-------------------|
| DNS | | |
| Load balancing | | |
| ... | | |

## Interview Talking Points

1. [PE-level insight that teaches something non-obvious]
2. ...
(5–7 total)

## PE Rubric Self-Assessment

```
PE Rubric Score:
 1. Problem reframing:     _/5
 2. Quantitative grounding: _/5
 3. Solution space:         _/5
 4. Trade-off rigor:        _/5
 5. Depth on demand:        _/5
 6. Failure modes:          _/5
 7. Production grounding:   _/5
 8. Organizational:         _/5
 9. Evolution vision:       _/5
10. Collaboration:          _/5

Average: _/5
Weakest dimension: [name] — [what would raise it]
```
