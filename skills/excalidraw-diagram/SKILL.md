---
name: excalidraw-diagram
description: >-
  Generate Excalidraw diagram JSON files that argue visually. Use when the user
  wants to visualize architectures, workflows, data flows, or concepts as
  .excalidraw files. Produces structured JSON that renders in any Excalidraw
  viewer (VS Code extension, excalidraw.com, embedded).
---

# Excalidraw Diagram Creator

Generate `.excalidraw` JSON files that **argue visually**, not just display
information.

## First-Time Setup

The skill includes a render pipeline for visual validation. Run once:

```bash
cd <path-to-this-skill>/references && uv sync && uv run playwright install chromium
```

Where `<path-to-this-skill>` is the directory containing this SKILL.md file.

## Customization

All colors live in `references/color-palette.md`. Edit it to change the visual
vocabulary. Everything else in this file is universal design methodology.

---

## Core Philosophy

**Diagrams should ARGUE, not DISPLAY.**

A diagram is a visual argument showing relationships, causality, and flow that
words alone cannot express. The shape should BE the meaning.

**The Isomorphism Test**: Remove all text. Does the structure alone communicate
the concept? If not, redesign.

**The Education Test**: Could someone learn something concrete from this diagram,
or does it just label boxes? A good diagram teaches.

---

## Depth Assessment (Do This First)

Before designing, determine what level of detail the diagram needs:

### Simple/Conceptual Diagrams

Use abstract shapes when:
- Explaining a mental model or philosophy
- The audience does not need technical specifics
- The concept IS the abstraction

### Comprehensive/Technical Diagrams

Use concrete examples when:
- Diagramming a real system, protocol, or architecture
- The diagram will be used to teach or explain
- The audience needs to understand what things actually look like
- You are showing how multiple technologies integrate

**For technical diagrams, include evidence artifacts** — code snippets, real
event names, actual JSON payloads, capacity numbers.

---

## Design Process (Do This BEFORE Generating JSON)

### Step 0: Assess Depth

Simple/conceptual or comprehensive/technical? This determines whether evidence
artifacts are needed.

### Step 1: Understand Deeply

For each concept, ask:
- What does this concept **DO**? (not what IS it)
- What relationships exist between concepts?
- What is the core transformation or flow?
- What would someone need to SEE to understand this?

### Step 2: Map Concepts to Visual Patterns

| If the concept... | Use this pattern |
|---|---|
| Spawns multiple outputs | **Fan-out** (radial arrows from center) |
| Combines inputs into one | **Convergence** (funnel, arrows merging) |
| Has hierarchy/nesting | **Tree** (lines + free-floating text) |
| Is a sequence of steps | **Timeline** (line + dots + labels) |
| Loops or improves continuously | **Spiral/Cycle** (arrow returning to start) |
| Is an abstract state or context | **Cloud** (overlapping ellipses) |
| Transforms input to output | **Assembly line** (before -> process -> after) |
| Compares two things | **Side-by-side** (parallel with contrast) |
| Separates into phases | **Gap/Break** (visual separation between sections) |

### Step 3: Ensure Variety

For multi-concept diagrams: each major concept must use a different visual
pattern. No uniform cards or grids.

### Step 4: Sketch the Flow

Before JSON, mentally trace how the eye moves through the diagram. There should
be a clear visual story — typically left-to-right or top-to-bottom.

### Step 5: Generate JSON Section-by-Section

See the Large Diagram Strategy below. Never generate the entire file in one pass.

### Step 6: Render and Validate (MANDATORY)

Run the render-view-fix loop until the diagram is clean. See the Render and
Validate section below.

---

## Multi-Zoom Architecture

Comprehensive diagrams operate at multiple zoom levels simultaneously:

### Level 1: Summary Flow
Simplified overview of the full pipeline at a glance.

### Level 2: Section Boundaries
Labeled regions that group related components into visual "rooms."

### Level 3: Detail Inside Sections
Evidence artifacts, capacity numbers, protocol annotations within each section.

For comprehensive diagrams, include all three levels.

---

## Container vs Free-Floating Text

**Not every piece of text needs a shape around it.** Default to free-floating
text. Add containers only when they serve a purpose.

| Use a Container When... | Use Free-Floating Text When... |
|---|---|
| It is the focal point of a section | It is a label or description |
| It needs visual grouping | It is supporting detail or metadata |
| Arrows need to connect to it | It describes something nearby |
| The shape itself carries meaning | Typography alone creates hierarchy |
| It represents a distinct "thing" | It is a title, subtitle, or annotation |

**The container test**: For each boxed element, ask "Would this work as
free-floating text?" If yes, remove the container.

---

## Visual Pattern Library

### Fan-Out (One-to-Many)
Central element with arrows radiating to multiple targets.
```
        o
       /
  [] --o
       \
        o
```

### Convergence (Many-to-One)
Multiple inputs merging through arrows to single output.
```
  o \
  o --> []
  o /
```

### Tree (Hierarchy)
Parent-child branching with connecting lines and free-floating text.
```
  label
  |-- label
  |   |-- label
  |   +-- label
  +-- label
```

### Timeline (Sequence)
Line with dots at intervals and free-floating labels.
```
  *--- Label 1
  |
  *--- Label 2
  |
  *--- Label 3
```

### Spiral/Cycle (Continuous Loop)
Elements in sequence with arrow returning to start.
```
  [] --> []
  ^       |
  |       v
  [] <-- []
```

### Assembly Line (Transformation)
Input -> Process -> Output with clear before/after.
```
  ooo -> [PROCESS] -> [][][]
  chaos               order
```

### Side-by-Side (Comparison)
Two parallel structures with visual contrast.

### Gap/Break (Separation)
Visual whitespace or barrier between sections.

---

## Shape Meaning

| Concept Type | Shape | Why |
|---|---|---|
| Labels, descriptions | **none** (free-floating text) | Typography creates hierarchy |
| Section titles | **none** (free-floating text) | Font size is enough |
| Markers on a timeline | small `ellipse` (10-20px) | Visual anchor |
| Start, trigger, input | `ellipse` | Soft, origin-like |
| End, output, result | `ellipse` | Completion |
| Decision, condition | `diamond` | Classic decision symbol |
| Process, action, service | `rectangle` | Contained action |
| Abstract state | overlapping `ellipse` | Fuzzy, cloud-like |
| Hierarchy node | lines + text (no boxes) | Structure through lines |

**Rule**: Default to no container. Add shapes only when they carry meaning.

---

## Color as Meaning

Colors encode information, not decoration. Every color choice comes from
`references/color-palette.md`.

Key principles:
- Each semantic purpose has a specific fill/stroke pair
- Free-floating text uses color for hierarchy (title/subtitle/body)
- Evidence artifacts use dark background + colored text
- Always pair a darker stroke with a lighter fill for contrast

**Do not invent new colors.** If a concept does not fit an existing semantic
category, use Primary/Neutral.

---

## Layout Principles

### Hierarchy Through Scale
- **Hero**: 300x150 — visual anchor, most important
- **Primary**: 180x90
- **Secondary**: 120x60
- **Small**: 60x40

### Whitespace = Importance
The most important element has the most empty space around it (200px+).

### Flow Direction
Guide the eye: left-to-right or top-to-bottom for sequences, radial for
hub-and-spoke.

### Connections Required
Position alone does not show relationships. If A relates to B, there must be
an arrow or line connecting them.

---

## Modern Aesthetics

- `roughness: 0` — Clean, crisp edges. Default for all professional diagrams.
- `strokeWidth: 2` — Standard for shapes and arrows. Use 1 for subtle lines.
- `opacity: 100` — Always. Use color and size for hierarchy, never transparency.
- `fontFamily: 3` — Monospace. Always.

---

## Large Diagram Strategy

**Build JSON one section at a time.** Never generate the entire file in a single
pass — it leads to truncation and worse quality.

### The Section-by-Section Workflow

**Phase 1: Build each section**

1. Create the base file with the JSON wrapper (`type`, `version`, `appState`,
   `files`) and the first section of elements.
2. Add one section per edit. Each section gets its own dedicated pass.
3. Use descriptive string IDs (e.g., `"gateway_rect"`, `"arrow_to_cache"`).
4. Namespace seeds by section (section 1 uses 100xxx, section 2 uses 200xxx).
5. Update cross-section bindings as you go.

**Phase 2: Review the whole**

After all sections are in place, read through the complete JSON and check:
- Are cross-section arrows bound correctly on both ends?
- Is overall spacing balanced?
- Do all IDs and bindings reference elements that exist?

**Phase 3: Render and validate**

Run the render-view-fix loop.

### Section Boundaries for Architecture Diagrams

- Section 1: Client layer + edge/CDN + gateway
- Section 2: Read path (services + caches)
- Section 3: Write path (collectors + event systems)
- Section 4: Data stores + background processing
- Section 5: Cross-cutting concerns (monitoring, annotations, legend)

---

## JSON Structure

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [...],
  "appState": {
    "viewBackgroundColor": "#ffffff",
    "gridSize": 20
  },
  "files": {}
}
```

Element templates are in `references/element-templates.md`. The full JSON
schema is in `references/json-schema.md`.

---

## Text Rules

The JSON `text` property contains ONLY readable words:

```json
{
  "id": "myElement1",
  "text": "API Gateway",
  "originalText": "API Gateway"
}
```

Settings: `fontSize: 16`, `fontFamily: 3`, `textAlign: "center"`,
`verticalAlign: "middle"`.

For titles: `fontSize: 20-24`. For annotations: `fontSize: 14`.

---

## Render and Validate (MANDATORY)

After generating the `.excalidraw` JSON, render it to PNG, view it, and fix
issues in a loop.

### How to Render

```bash
cd <path-to-this-skill>/references && uv run python render_excalidraw.py <path-to-file.excalidraw>
```

Where `<path-to-this-skill>` is the directory containing this SKILL.md file.

Outputs a PNG next to the `.excalidraw` file. Then use the Read tool on the PNG
to view it.

### The Loop

1. **Render and View** — Run the render script, then Read the PNG.

2. **Audit against your original vision** — Compare the rendered result to what
   you designed in Steps 1-4:
   - Does the visual structure match the conceptual structure?
   - Does each section use the pattern you intended?
   - Does the eye flow in the correct order?
   - Is visual hierarchy correct — hero elements dominant, supporting smaller?

3. **Check for visual defects:**
   - Text clipped by or overflowing its container
   - Text or shapes overlapping other elements
   - Arrows crossing through elements instead of routing around
   - Arrows landing on wrong element or pointing to empty space
   - Labels floating ambiguously
   - Uneven spacing between elements that should be evenly spaced
   - Text too small to read

4. **Fix** — Edit the JSON:
   - Widen containers for clipped text
   - Adjust x/y coordinates for spacing
   - Add intermediate waypoints to arrow points arrays
   - Reposition labels closer to their target
   - Resize elements to rebalance visual weight

5. **Re-render and re-view** — Run the render script again.

6. **Repeat** — Until the diagram passes both the vision check and defect check.
   Typically 2-4 iterations.

### When to Stop

- The rendered diagram matches the conceptual design
- No text is clipped, overlapping, or unreadable
- Arrows route cleanly and connect to the right elements
- Spacing is consistent and composition is balanced

---

## Quality Checklist

### Depth and Evidence (Technical Diagrams)
1. Evidence artifacts present (capacity numbers, protocol names, real data)?
2. Multi-zoom (summary + sections + detail)?
3. Concrete over abstract — real content shown, not just labeled boxes?

### Conceptual
4. Isomorphism — visual structure mirrors concept behavior?
5. Argument — diagram shows something text alone cannot?
6. Variety — each major concept uses a different visual pattern?

### Container Discipline
7. Minimal containers — could any boxed element work as free-floating text?
8. Lines as structure — tree/timeline using lines + text, not boxes?
9. Typography hierarchy — font size and color creating visual levels?

### Structural
10. Every relationship has an arrow or line?
11. Clear visual path for the eye to follow?
12. Important elements are larger/more isolated?

### Technical
13. `fontFamily: 3`, `roughness: 0`, `opacity: 100`?
14. Text contains only readable words?
15. All IDs unique and descriptive?

### Visual Validation
16. Rendered to PNG and visually inspected?
17. No overlapping, clipped, or unreadable text?
18. Arrows land correctly, spacing is consistent?
