# System Design Interview Skill

An open [Agent Skill](https://agentskills.io) that generates **Principal-Engineer-grade** system design interview preparation documents. Works with Cursor, Codex CLI, Claude Code, Gemini CLI, GitHub Copilot, and any SKILL.md-compatible AI agent.

## What it does

Say "design a URL shortener" (or any system design problem) to your AI agent. The skill produces **10 artifacts** through a rigorous 6-phase generate-evaluate-fix loop:

| File | Content |
|------|---------|
| `01-requirements.md` | Functional requirements, capacity estimation, scope |
| `02-non-functional-requirements.md` | Latency budgets, error budgets, consistency model, runbooks |
| `03-entities.md` | Domain objects, relationships, state machines |
| `04-api-design.md` | Concrete REST/gRPC contracts with request/response shapes |
| `05-schema.md` | Storage schema, indexes, sharding strategy |
| `06-high-level-design.md` | Architecture with write/read/failure/deploy flows |
| `06-high-level-design.excalidraw` | Visual companion diagram |
| `07-deep-dives.md` | 4-6 component deep dives with tiered solutions |
| `08-bottlenecks-and-tradeoffs.md` | Failure matrix, anti-patterns, evolution roadmap |
| `09-eval-report.md` | Machine-verified PASS/FAIL quality report |

Every design is validated against **27 gate criteria**, **5 cross-file consistency checks**, and a **10-dimension PE rubric** (avg >= 4.5, no dimension < 4).

## Quick start

[Install](#installation) the skill once, then paste any prompt below into your agent.
The skill activates automatically — no slash command required.

### Direct design

Start with any system design problem:

> Design a distributed rate limiter
>
> Design an in-memory cache with LRU eviction
>
> Design a URL shortener

### Company-specific

Tailor the design to an interview target:

> System design for Google — design a news feed
>
> System design for Amazon — design an order fulfillment system
>
> System design for Databricks — design a top-K trending articles system

### PE interview prep

Ask for Principal-Engineer-grade depth and rubric scoring:

> Prepare a chat system for PE interview
>
> Prepare a distributed cache for PE interview at Meta
>
> System design interview — design a payment gateway

### Break down an existing system

Reverse-engineer or decompose a real product:

> Break down how Slack handles real-time messaging
>
> Break down the architecture of a ride-sharing dispatch system
>
> Break down a notification system like Firebase Cloud Messaging

### Mix and match

Combine any pattern:

| Pattern | Example |
|---------|---------|
| `Design a [system]` | Design a rate limiter |
| `System design for [company] — design a [system]` | System design for Google — design a news feed |
| `Prepare [system] for PE interview` | Prepare a URL shortener for PE interview |
| `Break down [system or product]` | Break down a chat system |
| `System design interview — design a [system]` | System design interview — design a search autocomplete |

**Output:** 10 files in `system-design/<problem-name>/` under your project root.

## Installation

Works with Cursor, Claude Code, Codex, Gemini CLI, GitHub Copilot, and any
[Agent Skills](https://agentskills.io)-compatible agent. Pick either method:

```bash
# Option A — open skills ecosystem (Node.js required)
npx skills add iamurali/system-design-skill --all -g -y

# Option B — zero dependencies (bash + git/curl)
curl -fsSL https://raw.githubusercontent.com/iamurali/system-design-skill/main/install.sh | bash
```

Both install `system-design-interview` and `excalidraw-diagram` to
`~/.agents/skills/` — the vendor-neutral path recognized by all major agents.

### Project-local

```bash
npx skills add iamurali/system-design-skill --all -y
# or
curl -fsSL https://raw.githubusercontent.com/iamurali/system-design-skill/main/install.sh | bash -s -- --project
```

### Update

```bash
npx skills update
# or
curl -fsSL https://raw.githubusercontent.com/iamurali/system-design-skill/main/install.sh | bash -s -- --update
```

### Optional: diagram rendering

PNG rendering for Excalidraw diagrams requires [uv](https://docs.astral.sh/uv/)
and Playwright. Run once after install:

```bash
curl -fsSL https://raw.githubusercontent.com/iamurali/system-design-skill/main/install.sh | bash -s -- --excalidraw
```

Or manually:

```bash
cd ~/.agents/skills/excalidraw-diagram/references && uv sync && uv run playwright install chromium
```

### Cursor users

You can also install from the [Cursor Marketplace](https://cursor.com/marketplace)
or add a remote rule (`https://github.com/iamurali/system-design-skill`) — no
terminal required.

## Architecture

```
skills/
  system-design-interview/
    SKILL.md                    # Entry point (Agent Skills standard)
    references/
      orchestrator.md           # 6-phase generate-evaluate-fix loop
      reasoning-engine.md       # Design methodology + failure modes
      principal-engineer-bar.md # 10-dimension PE rubric
      building-blocks-index.md  # L0-L7 component catalog
      company-profiles.md       # Interview formats by company
      problem-bank.md           # 30+ curated problems
      tradeoff-framework.md     # 3-question trade-off method
      numbers-to-know.md        # Latency, QPS, storage references
    scripts/
      validator/                # Python CLI (stdlib only, zero deps)
    assets/
      exemplars/                # Calibration examples
  excalidraw-diagram/
    SKILL.md                    # Companion skill for visual diagrams
    references/                 # Color palette, templates, render pipeline
```

The skill uses **progressive disclosure** to manage context efficiently:
1. Agent reads only skill metadata at startup (~100 tokens)
2. Full SKILL.md loads when a system design task is detected
3. Reference files load just-in-time per phase (never all 7 at once)
4. Context checkpoint after Phase 3 compresses prior work to ~20 lines

## Validator

The included Python validator produces machine-verified eval reports. It uses
stdlib only (no external dependencies).

```bash
cd skills/system-design-interview/scripts
python3 -m validator validate /path/to/system-design/your-problem/
```

## The Principal Engineer bar

This skill is calibrated for PE-level interviews. PE is not "Staff but more" --
it is a qualitatively different signal:

- **Reframes before solving.** Questions the problem itself.
- **Sees the full solution space.** 2-3 architectures with forces that pick.
- **Brings production war stories.** Failure modes at real scale.
- **Thinks organizationally.** Team ownership, blast radius, oncall burden.
- **Anticipates the 3-5 year arc.** What breaks at 10x, 100x, 1000x.
- **Teaches the interviewer something.** Novel, non-obvious insights.
- **YAGNI at scale.** Cheapest design that meets constraints.

## Compatibility

| Platform | Status | Install method |
|----------|--------|----------------|
| Cursor | Supported | `npx skills` / `install.sh` / Marketplace |
| Claude Code | Supported | `npx skills` / `install.sh` |
| Codex CLI | Supported | `npx skills` / `install.sh` |
| Gemini CLI | Supported | `npx skills` / `install.sh` |
| GitHub Copilot | Supported | `npx skills` / `install.sh` |
| Any SKILL.md agent | Supported | `~/.agents/skills/` |

**Requirements:** Python 3.10+ (for validator only). Excalidraw rendering
requires [uv](https://docs.astral.sh/uv/) + Playwright (optional).

## License

MIT
