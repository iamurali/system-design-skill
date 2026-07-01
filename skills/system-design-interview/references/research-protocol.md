# Research Protocol -- Industry-Standard Gap Filling

Use this protocol when the Interviewer reports at least one **Critical** or
**Major** finding. The Research agent does not rewrite the design directly. It
returns grounded solutions that the generator uses to revise the affected
sections.

Research MUST NOT run for isolated minor findings. Minor findings are fixed
locally unless they repeat across phases and form a pattern.

---

## Inputs

The Research agent receives:

- The Interviewer findings marked `Research required: yes`
- The relevant generated files or sections
- The context checkpoint with scale, NFRs, entities, access patterns, and known
  constraints
- The target level: DE, PE, or Senior Staff/Principal
- The target company, if named by the user

Do not research the entire system. Research only the major/critical gaps.

---

## Research Sources

Use a hybrid approach:

1. **Reference packs first**
   - `references/building-blocks-index.md` for component options and omitted
     layers
   - `references/company-profiles.md` for company-specific bar and system
     references
   - `references/faang-interview-patterns.md` for world-class interview calibration
   - `references/numbers-to-know.md` for latency/QPS/storage plausibility
   - `references/tradeoff-framework.md` for decision framing

2. **External research for gaps**
   - Engineering blogs from credible operators (Google, Meta, Netflix, Uber,
     Stripe, Cloudflare, LinkedIn, Amazon, GitHub, etc.)
   - Papers and public system docs when algorithm/protocol depth is needed
   - Vendor docs only for concrete behavior, limits, failure modes, or operating
     constraints
   - Incident reports and postmortems for failure-mode grounding

Prefer primary sources over summaries. If a source only repeats generic advice,
do not cite it.

---

## Level Calibration

### DE / Senior Engineer

Return practical, correct implementation details:
- Concrete API/schema/index choices
- Common failure modes and mitigations
- Operational defaults that are safe enough for production
- Clear tradeoffs but not necessarily full evolution strategy

### Staff Engineer

Add cross-component reasoning:
- How choices affect neighboring systems
- Migration paths and ownership boundaries
- Operational metrics and alerting
- What changes at 10x
- Why simpler alternatives are not sufficient

### Senior Staff / Principal Engineer

Add business and platform judgment:
- Multiple viable architectures and the forces that select one
- What breaks at 10x/100x/1000x
- Team ownership, blast radius, oncall burden
- Failure stories, incidents, and recovery posture
- Non-obvious simplifications or constraints that avoid unnecessary complexity

---

## Output Format

Append the Research section to `10-interview-transcript.md`:

```markdown
## Research Findings -- Phase [N or Final]

### Research Scope
- Triggered by findings: I-1, I-3
- Target level: PE | Senior Staff | DE
- Research mode: reference pack + web

### Finding I-[number]: [short title]

#### Industry Standard
- Pattern:
- Where used:
- Why it applies to this design:
- Where it does not apply:

#### Evidence
- Source: [title](url), org, year
- Key point:
- Confidence: high | medium | low

#### Revision Guidance
- File/section to change:
- Add:
- Remove or weaken:
- New tradeoff:
- New failure mode or bottleneck:
```

If no external search was needed because the local reference packs were
sufficient, say so explicitly:

```markdown
Research mode: reference pack only
External sources: none needed
```

---

## Revision Guidance Rules

- Do not prescribe a bigger system unless a number forces it.
- Map every recommendation to the current design's scale and NFRs.
- Include the "what would make us change" condition for every recommended
  technology or algorithm.
- Include an explicit downgrade path when the PE-grade solution is too complex
  for current scale.
- Cite enough evidence for the generator to revise confidently, but avoid
  dumping full source summaries.
- If the Interviewer finding is wrong, say so and explain why with evidence.

---

## Research Quality Bar

A Research finding is acceptable only if it has:

- A named pattern or mechanism
- A source or local reference
- A reason it applies to this system's constraints
- A reason it might not apply
- Concrete revision guidance

A finding is incomplete if it only says "use Kafka", "add cache", "shard the
database", or cites a company without explaining the underlying mechanics.
