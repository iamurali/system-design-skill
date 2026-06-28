# Color Palette — System Architecture

All colors and semantic styles for Excalidraw diagrams. This is the single
source of truth for every color choice in generated diagrams.

---

## Shape Colors (Semantic)

Colors encode the role of a component, not decoration. Each semantic purpose has
a fill/stroke pair.

| Semantic Purpose | Fill | Stroke | Use For |
|---|---|---|---|
| Client/External | `#fed7aa` | `#c2410c` | Mobile apps, browsers, third-party APIs |
| Stateless Service | `#dbeafe` | `#1e40af` | API gateway, feed service, auth service |
| Stateful Store | `#a7f3d0` | `#047857` | PostgreSQL, DynamoDB, S3, HDFS |
| Cache | `#bfdbfe` | `#2563eb` | Redis, Memcached, CDN edge cache |
| Async/Event System | `#ddd6fe` | `#6d28d9` | Kafka, SQS, RabbitMQ, event bus |
| Background Worker | `#fef3c7` | `#b45309` | Cron jobs, batch pipelines, ML training |
| Error/Degradation | `#fecaca` | `#b91c1c` | DLQ, circuit breaker, fallback path |
| Decision/Router | `#fef9c3` | `#92400e` | Load balancer, feature flag, router |

**Rule**: Always pair a darker stroke with a lighter fill for contrast.

---

## Text Colors (Hierarchy)

Use color on free-floating text to create visual hierarchy without containers.

| Level | Color | Use For |
|---|---|---|
| Title | `#1e40af` | Section headings, major labels |
| Subtitle | `#3b82f6` | Subheadings, secondary labels |
| Body/Detail | `#64748b` | Descriptions, annotations, metadata |
| On light fills | `#374151` | Text inside light-colored shapes |
| On dark fills | `#ffffff` | Text inside dark-colored shapes |

---

## Evidence Artifact Colors

For code snippets, JSON examples, and capacity numbers inside technical diagrams.

| Artifact | Background | Text Color |
|---|---|---|
| Code snippet | `#1e293b` | Language-appropriate syntax colors |
| JSON/data example | `#1e293b` | `#22c55e` (green) |
| Capacity annotation | transparent | `#dc2626` (red, bold) |

---

## Arrow and Line Colors

| Element | Color | Style |
|---|---|---|
| Sync call arrow | Source element's stroke color | `strokeStyle: "solid"` |
| Async/fire-and-forget arrow | `#6d28d9` (purple) | `strokeStyle: "dashed"` |
| Structural lines (dividers, trees) | `#64748b` (slate) | `strokeStyle: "solid"` |
| Marker dots (fill + stroke) | `#3b82f6` (blue) | Small ellipse, 10-12px |

---

## Background

| Property | Value |
|---|---|
| Canvas background | `#ffffff` |
