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

Say any of these to your AI agent:

- "Design a distributed rate limiter"
- "System design for Google -- design a news feed"
- "Prepare a URL shortener for PE interview"
- "Break down a chat system"

The skill activates automatically based on your prompt.

## Installation

### Cursor (Marketplace plugin)

Install from the [Cursor Marketplace](https://cursor.com/marketplace) or add as a remote rule:

1. Open **Customize** in the sidebar
2. Go to **Rules** and click **Add Rule**
3. Select **Remote Rule (Github)**
4. Enter: `https://github.com/iamurali/system-design-skill`

### Cursor (local)

```bash
cd your-project
git clone https://github.com/iamurali/system-design-skill.git .cursor/plugins/system-design-skill
```

### Codex CLI

```bash
git clone https://github.com/iamurali/system-design-skill.git ~/.codex/skills/system-design-skill
```

Or symlink into your project:

```bash
cd your-project
mkdir -p .agents/skills
ln -s /path/to/system-design-skill/skills/system-design-interview .agents/skills/system-design-interview
ln -s /path/to/system-design-skill/skills/excalidraw-diagram .agents/skills/excalidraw-diagram
```

### Claude Code

```bash
# Personal (all projects)
git clone https://github.com/iamurali/system-design-skill.git ~/.claude/skills/system-design-skill

# Or project-specific
cd your-project
mkdir -p .claude/skills
ln -s /path/to/system-design-skill/skills/system-design-interview .claude/skills/system-design-interview
ln -s /path/to/system-design-skill/skills/excalidraw-diagram .claude/skills/excalidraw-diagram
```

### Gemini CLI / GitHub Copilot

```bash
cd your-project
mkdir -p .agents/skills
ln -s /path/to/system-design-skill/skills/system-design-interview .agents/skills/system-design-interview
ln -s /path/to/system-design-skill/skills/excalidraw-diagram .agents/skills/excalidraw-diagram
```

### Manual (any agent)

Clone the repo anywhere and point your agent at `skills/system-design-interview/SKILL.md`.

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
| Cursor | Supported | Marketplace plugin or remote rule |
| Codex CLI | Supported | Clone to `~/.codex/skills/` |
| Claude Code | Supported | Clone to `~/.claude/skills/` |
| Gemini CLI | Supported | Clone to `.agents/skills/` |
| GitHub Copilot | Supported | Clone to `.agents/skills/` |
| Any SKILL.md agent | Supported | Point at SKILL.md |

**Requirements:** Python 3.10+ (for validator only). Excalidraw rendering
requires [uv](https://docs.astral.sh/uv/) + Playwright (optional).

## License

MIT
