# System Design Interview Skill

This repository provides a Principal-Engineer-grade system design interview
skill. It is distributed as an open Agent Skill compatible with Cursor, Codex
CLI, Claude Code, Gemini CLI, GitHub Copilot, and any SKILL.md-compatible
agent.

To install: see [README Installation](README.md#installation).

## Activation

When the user says "design a system", "system design for [company]", "prepare
[system] for PE interview", "break down [system]", "system design interview",
or names any system design problem (URL shortener, distributed cache, news
feed, rate limiter, top-K, chat system, etc.), activate the
`system-design-interview` skill.

## How to execute

1. Read `skills/system-design-interview/SKILL.md`. It is the skill entry point.
2. Follow the SKILL.md instructions -- it will direct you to read the
   orchestrator and reference files as needed.
3. Output goes in `system-design/<problem-name>/` relative to the user's
   project root (not this repository).

## Skills in this repository

| Skill | Purpose |
|-------|---------|
| `skills/system-design-interview/` | Main skill: 6-phase design loop with quality gates |
| `skills/excalidraw-diagram/` | Companion: visual `.excalidraw` diagram generation |
