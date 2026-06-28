# Excalidraw JSON Schema

Reference for the `.excalidraw` file format. Use this when generating or
validating Excalidraw JSON.

---

## Top-Level Structure

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

- `type` must be `"excalidraw"`
- `version` must be `2`
- `elements` is the array of all shapes, text, arrows, and lines
- `appState.viewBackgroundColor` controls canvas background
- `files` is for embedded images (usually empty `{}`)

---

## Element Types

| Type | Use For |
|---|---|
| `rectangle` | Services, processes, components, containers |
| `ellipse` | Entry/exit points, external systems, marker dots |
| `diamond` | Decisions, conditionals, routers |
| `arrow` | Directed connections between shapes |
| `line` | Non-directed connections, dividers, tree structures |
| `text` | Labels inside shapes or free-floating annotations |
| `frame` | Grouping containers (optional) |

---

## Common Properties (All Elements)

| Property | Type | Description |
|---|---|---|
| `id` | string | Unique identifier (use descriptive names) |
| `type` | string | Element type from table above |
| `x`, `y` | number | Position in pixels (top-left corner) |
| `width`, `height` | number | Size in pixels |
| `strokeColor` | string | Border/outline color (hex) |
| `backgroundColor` | string | Fill color (hex or `"transparent"`) |
| `fillStyle` | string | `"solid"`, `"hachure"`, `"cross-hatch"` |
| `strokeWidth` | number | 1, 2, or 4 |
| `strokeStyle` | string | `"solid"`, `"dashed"`, `"dotted"` |
| `roughness` | number | 0 (smooth), 1 (hand-drawn), 2 (rough) |
| `opacity` | number | 0-100 (always use 100) |
| `angle` | number | Rotation in radians (usually 0) |
| `seed` | number | Random seed for rendering consistency |
| `version` | number | Element version (use 1 for new elements) |
| `versionNonce` | number | Unique nonce for version tracking |
| `isDeleted` | boolean | Soft-delete flag (always `false`) |
| `groupIds` | array | IDs of groups this element belongs to |
| `frameId` | string/null | ID of containing frame |
| `boundElements` | array/null | Elements bound to this one |
| `link` | string/null | URL link (usually `null`) |
| `locked` | boolean | Whether element is locked |

---

## Text-Specific Properties

| Property | Type | Description |
|---|---|---|
| `text` | string | The display text (readable words only) |
| `originalText` | string | Same as `text` |
| `fontSize` | number | Size in pixels (14-24 recommended) |
| `fontFamily` | number | 3 = monospace (always use this) |
| `textAlign` | string | `"left"`, `"center"`, `"right"` |
| `verticalAlign` | string | `"top"`, `"middle"`, `"bottom"` |
| `containerId` | string/null | ID of parent shape (null if free-floating) |
| `lineHeight` | number | Line height multiplier (use 1.25) |

---

## Arrow-Specific Properties

| Property | Type | Description |
|---|---|---|
| `points` | array | Array of `[x, y]` coordinates relative to element position |
| `startBinding` | object/null | Connection to start shape |
| `endBinding` | object/null | Connection to end shape |
| `startArrowhead` | string/null | `null`, `"arrow"`, `"bar"`, `"dot"`, `"triangle"` |
| `endArrowhead` | string/null | Same options as startArrowhead |

---

## Binding Object Format

```json
{
  "elementId": "target_shape_id",
  "focus": 0,
  "gap": 2
}
```

- `elementId`: the ID of the shape being connected to
- `focus`: where on the shape edge the arrow attaches (-1 to 1, 0 = center)
- `gap`: pixel gap between arrow endpoint and shape edge

---

## Rectangle Roundness

For rounded corners (services, modern components):

```json
"roundness": {"type": 3}
```

For sharp corners (databases, storage): omit `roundness` or set to `null`.

---

## Points Array (Arrows and Lines)

Points are relative to the element's `x`, `y` position:

- Horizontal arrow: `[[0, 0], [200, 0]]`
- Vertical arrow: `[[0, 0], [0, 150]]`
- Diagonal arrow: `[[0, 0], [150, 100]]`
- Curved arrow (3 points): `[[0, 0], [75, -50], [150, 0]]`
- Multi-segment: `[[0, 0], [100, 0], [100, 80], [200, 80]]`

---

## Coordinate System

- Origin (0, 0) is at the top-left of the canvas
- X increases to the right
- Y increases downward
- Elements are positioned by their top-left corner
- Negative coordinates are valid (canvas extends in all directions)

---

## Size Guidelines

| Element Role | Width | Height |
|---|---|---|
| Hero component | 250-350 | 120-180 |
| Primary service | 160-200 | 80-100 |
| Secondary component | 100-140 | 50-70 |
| Small marker/dot | 10-16 | 10-16 |
| Annotation text | auto | 20-30 |

---

## Validation Rules

A valid `.excalidraw` file must satisfy:

1. Top-level `type` is `"excalidraw"`
2. `elements` is a non-empty array
3. Every element has a unique `id`
4. Every `containerId` references an existing element
5. Every binding `elementId` references an existing element
6. Every element in `boundElements` arrays exists in `elements`
7. Text elements with `containerId` have matching entry in parent's `boundElements`
8. Arrow `points` arrays have at least 2 points
