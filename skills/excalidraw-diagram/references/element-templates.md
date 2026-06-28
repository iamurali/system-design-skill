# Element Templates

JSON templates for each Excalidraw element type. The `strokeColor` and
`backgroundColor` values are placeholders — always pull actual colors from
`color-palette.md` based on the element's semantic purpose.

---

## Rectangle (Service, Process, Component)

```json
{
  "type": "rectangle",
  "id": "service_name",
  "x": 100,
  "y": 100,
  "width": 180,
  "height": 90,
  "strokeColor": "<stroke from palette>",
  "backgroundColor": "<fill from palette>",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "angle": 0,
  "seed": 100001,
  "version": 1,
  "versionNonce": 100002,
  "isDeleted": false,
  "groupIds": [],
  "frameId": null,
  "boundElements": [{"id": "text_inside_id", "type": "text"}],
  "link": null,
  "locked": false,
  "roundness": {"type": 3}
}
```

For dashed borders (ephemeral/optional components): `"strokeStyle": "dashed"`.

---

## Text (Centered in a Shape)

```json
{
  "type": "text",
  "id": "text_inside_id",
  "x": 120,
  "y": 130,
  "width": 140,
  "height": 25,
  "text": "API Gateway",
  "originalText": "API Gateway",
  "fontSize": 16,
  "fontFamily": 3,
  "textAlign": "center",
  "verticalAlign": "middle",
  "strokeColor": "<text color from palette — use 'on light fills' or 'on dark fills'>",
  "backgroundColor": "transparent",
  "fillStyle": "solid",
  "strokeWidth": 1,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "angle": 0,
  "seed": 100003,
  "version": 1,
  "versionNonce": 100004,
  "isDeleted": false,
  "groupIds": [],
  "frameId": null,
  "boundElements": null,
  "link": null,
  "locked": false,
  "containerId": "service_name",
  "lineHeight": 1.25
}
```

---

## Free-Floating Text (Label, Title, Annotation)

```json
{
  "type": "text",
  "id": "label_name",
  "x": 100,
  "y": 100,
  "width": 200,
  "height": 25,
  "text": "Section Title",
  "originalText": "Section Title",
  "fontSize": 20,
  "fontFamily": 3,
  "textAlign": "left",
  "verticalAlign": "top",
  "strokeColor": "<title/subtitle/body color from palette>",
  "backgroundColor": "transparent",
  "fillStyle": "solid",
  "strokeWidth": 1,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "angle": 0,
  "seed": 100005,
  "version": 1,
  "versionNonce": 100006,
  "isDeleted": false,
  "groupIds": [],
  "frameId": null,
  "boundElements": null,
  "link": null,
  "locked": false,
  "containerId": null,
  "lineHeight": 1.25
}
```

Font size guide: Title = 20-24, Subtitle = 16-18, Body/annotation = 14.

---

## Arrow (Connection Between Elements)

```json
{
  "type": "arrow",
  "id": "arrow_source_to_target",
  "x": 282,
  "y": 145,
  "width": 118,
  "height": 0,
  "strokeColor": "<source element's stroke color from palette>",
  "backgroundColor": "transparent",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "angle": 0,
  "seed": 100007,
  "version": 1,
  "versionNonce": 100008,
  "isDeleted": false,
  "groupIds": [],
  "frameId": null,
  "boundElements": null,
  "link": null,
  "locked": false,
  "points": [[0, 0], [118, 0]],
  "startBinding": {"elementId": "source_id", "focus": 0, "gap": 2},
  "endBinding": {"elementId": "target_id", "focus": 0, "gap": 2},
  "startArrowhead": null,
  "endArrowhead": "arrow"
}
```

For async arrows: `"strokeStyle": "dashed"`.
For curves: use 3+ points in `points` array.
For bidirectional: `"startArrowhead": "arrow"`.

---

## Line (Structural — Not an Arrow)

```json
{
  "type": "line",
  "id": "divider_line",
  "x": 100,
  "y": 100,
  "width": 0,
  "height": 200,
  "strokeColor": "#64748b",
  "backgroundColor": "transparent",
  "fillStyle": "solid",
  "strokeWidth": 1,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "angle": 0,
  "seed": 100009,
  "version": 1,
  "versionNonce": 100010,
  "isDeleted": false,
  "groupIds": [],
  "frameId": null,
  "boundElements": null,
  "link": null,
  "locked": false,
  "points": [[0, 0], [0, 200]]
}
```

For horizontal lines: `"points": [[0, 0], [400, 0]]`.
For dashed dividers: `"strokeStyle": "dashed"`.

---

## Ellipse (Small Marker Dot)

```json
{
  "type": "ellipse",
  "id": "dot_marker",
  "x": 94,
  "y": 94,
  "width": 12,
  "height": 12,
  "strokeColor": "#3b82f6",
  "backgroundColor": "#3b82f6",
  "fillStyle": "solid",
  "strokeWidth": 1,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "angle": 0,
  "seed": 100011,
  "version": 1,
  "versionNonce": 100012,
  "isDeleted": false,
  "groupIds": [],
  "frameId": null,
  "boundElements": null,
  "link": null,
  "locked": false
}
```

For larger ellipses (external systems, start/end points): increase width/height
to 80-120px and add `"roundness": null`.

---

## Binding Rules

When an arrow connects two shapes:

1. The arrow's `startBinding.elementId` = source shape's `id`
2. The arrow's `endBinding.elementId` = target shape's `id`
3. The source shape's `boundElements` array must include `{"id": "arrow_id", "type": "arrow"}`
4. The target shape's `boundElements` array must include `{"id": "arrow_id", "type": "arrow"}`

Both ends must be updated for the connection to render correctly.

---

## ID Naming Convention

Use descriptive string IDs namespaced by section:

- `"gateway_rect"` — the API gateway rectangle
- `"gateway_text"` — text inside the gateway
- `"arrow_gateway_to_feed"` — arrow from gateway to feed service
- `"legend_title"` — the legend section title

Namespace seeds by section number (section 1 = 100xxx, section 2 = 200xxx, etc.)
to avoid collisions when building incrementally.
