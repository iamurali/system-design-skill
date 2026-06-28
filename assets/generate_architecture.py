#!/usr/bin/env python3
"""Generate assets/architecture.excalidraw for README hero diagram."""

from __future__ import annotations

import json
from pathlib import Path

# Colors from excalidraw-diagram/references/color-palette.md
C = {
    "client_fill": "#fed7aa",
    "client_stroke": "#c2410c",
    "service_fill": "#dbeafe",
    "service_stroke": "#1e40af",
    "store_fill": "#a7f3d0",
    "store_stroke": "#047857",
    "async_fill": "#ddd6fe",
    "async_stroke": "#6d28d9",
    "worker_fill": "#fef3c7",
    "worker_stroke": "#b45309",
    "decision_fill": "#fef9c3",
    "decision_stroke": "#92400e",
    "title": "#1e40af",
    "subtitle": "#3b82f6",
    "body": "#64748b",
    "on_light": "#374151",
    "slate": "#64748b",
}

_nonce = 100000


def nid(prefix: str) -> str:
    global _nonce
    _nonce += 1
    return f"{prefix}_{_nonce}"


def rect(
    rid: str,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    fill: str,
    stroke: str,
    dashed: bool = False,
) -> dict:
    return {
        "type": "rectangle",
        "id": rid,
        "x": x,
        "y": y,
        "width": w,
        "height": h,
        "strokeColor": stroke,
        "backgroundColor": fill,
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "dashed" if dashed else "solid",
        "roughness": 0,
        "opacity": 100,
        "angle": 0,
        "seed": _nonce,
        "version": 1,
        "versionNonce": _nonce + 1,
        "isDeleted": False,
        "groupIds": [],
        "frameId": None,
        "boundElements": [],
        "link": None,
        "locked": False,
        "roundness": {"type": 3},
    }


def text(
    tid: str,
    x: float,
    y: float,
    w: float,
    h: float,
    content: str,
    *,
    color: str = C["on_light"],
    size: int = 16,
    align: str = "center",
    valign: str = "middle",
    container: str | None = None,
) -> dict:
    return {
        "type": "text",
        "id": tid,
        "x": x,
        "y": y,
        "width": w,
        "height": h,
        "text": content,
        "originalText": content,
        "fontSize": size,
        "fontFamily": 3,
        "textAlign": align,
        "verticalAlign": valign,
        "strokeColor": color,
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "angle": 0,
        "seed": _nonce,
        "version": 1,
        "versionNonce": _nonce + 1,
        "isDeleted": False,
        "groupIds": [],
        "frameId": None,
        "boundElements": None,
        "link": None,
        "locked": False,
        "containerId": container,
        "lineHeight": 1.25,
    }


def arrow(
    aid: str,
    x: float,
    y: float,
    points: list[list[float]],
    *,
    stroke: str,
    dashed: bool = False,
    label: str | None = None,
) -> list[dict]:
    els: list[dict] = [
        {
            "type": "arrow",
            "id": aid,
            "x": x,
            "y": y,
            "width": abs(points[-1][0]),
            "height": abs(points[-1][1]) or 1,
            "strokeColor": stroke,
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 2,
            "strokeStyle": "dashed" if dashed else "solid",
            "roughness": 0,
            "opacity": 100,
            "angle": 0,
            "seed": _nonce,
            "version": 1,
            "versionNonce": _nonce + 1,
            "isDeleted": False,
            "groupIds": [],
            "frameId": None,
            "boundElements": None,
            "link": None,
            "locked": False,
            "points": points,
            "startBinding": None,
            "endBinding": None,
            "startArrowhead": None,
            "endArrowhead": "arrow",
            "lastCommittedPoint": None,
        }
    ]
    if label:
        lx = x + points[-1][0] / 2 - 30
        ly = y + points[-1][1] / 2 - 10
        els.append(
            text(nid("lbl"), lx, ly, 80, 20, label, color=C["body"], size=12, align="center")
        )
    return els


def box_with_text(
    rid: str,
    x: float,
    y: float,
    w: float,
    h: float,
    content: str,
    *,
    fill: str,
    stroke: str,
    dashed: bool = False,
    tsize: int = 15,
    tcolor: str = C["on_light"],
) -> list[dict]:
    tid = nid("txt")
    r = rect(rid, x, y, w, h, fill=fill, stroke=stroke, dashed=dashed)
    r["boundElements"] = [{"id": tid, "type": "text"}]
    pad = 8
    t = text(
        tid,
        x + pad,
        y + pad,
        w - 2 * pad,
        h - 2 * pad,
        content,
        color=tcolor,
        size=tsize,
        container=rid,
    )
    return [r, t]


def main() -> None:
    elements: list[dict] = []
    W = 1500

    # Title
    elements.append(
        text(
            "title",
            40,
            20,
            W - 80,
            40,
            "System Design Interview Skill — How It Works",
            color=C["title"],
            size=28,
            align="center",
            valign="top",
        )
    )

    # Layer 1: Trigger
    elements.extend(
        box_with_text(
            "user",
            80,
            80,
            280,
            70,
            'User prompt\n"Design a URL shortener"',
            fill=C["client_fill"],
            stroke=C["client_stroke"],
            tsize=14,
        )
    )
    elements.extend(
        box_with_text(
            "agent",
            520,
            80,
            900,
            70,
            "Any SKILL.md agent — Cursor · Claude Code · Codex · Gemini · Copilot",
            fill=C["client_fill"],
            stroke=C["client_stroke"],
            tsize=14,
        )
    )
    elements.extend(arrow("a1", 360, 115, [[0, 0], [150, 0]], stroke=C["client_stroke"], label="activates"))

    # Layer 2: Skill entry
    elements.extend(
        box_with_text(
            "skill_meta",
            80,
            190,
            420,
            80,
            "SKILL.md metadata (~100 tokens)\n→ full skill on trigger",
            fill=C["service_fill"],
            stroke=C["service_stroke"],
            tsize=14,
        )
    )
    elements.extend(
        box_with_text(
            "orchestrator",
            560,
            190,
            860,
            80,
            "orchestrator.md — 6-phase generate → evaluate → fix loop",
            fill=C["service_fill"],
            stroke=C["service_stroke"],
            tsize=14,
        )
    )
    elements.extend(arrow("a2", 500, 230, [[0, 0], [50, 0]], stroke=C["service_stroke"]))

    # Layer 3: 6-phase loop container
    loop_x, loop_y, loop_w, loop_h = 80, 310, 980, 150
    loop_id = "phase_loop"
    loop_rect = rect(loop_id, loop_x, loop_y, loop_w, loop_h, fill=C["service_fill"], stroke=C["service_stroke"])
    loop_rect["boundElements"] = [{"id": "phase_loop_txt", "type": "text"}]
    elements.append(loop_rect)
    elements.append(
        text(
            "phase_loop_txt",
            loop_x + 16,
            loop_y + 12,
            loop_w - 32,
            36,
            "6-Phase Inner Loop — generate → evaluate → fix (max 2× per gate)",
            color=C["service_stroke"],
            size=16,
            align="left",
            valign="top",
            container=loop_id,
        )
    )

    phases = [
        ("1\nReq", 100),
        ("2\nNFR", 250),
        ("3\nAPI", 400),
        ("checkpoint", 550),
        ("4\nHLD", 700),
        ("5\nDive", 850),
        ("6\nTrade", 1000),
    ]
    for label, px in phases:
        if label == "checkpoint":
            elements.append(
                text(
                    nid("cp"),
                    px,
                    loop_y + 70,
                    120,
                    40,
                    "Context\ncheckpoint",
                    color=C["body"],
                    size=12,
                    align="center",
                )
            )
        else:
            elements.extend(
                box_with_text(
                    nid("ph"),
                    px,
                    loop_y + 55,
                    110,
                    70,
                    label,
                    fill="#ffffff",
                    stroke=C["service_stroke"],
                    tsize=13,
                )
            )

    # Phase arrows inside loop
    for sx in [210, 360, 510, 670, 820, 970]:
        elements.extend(
            arrow(nid("pa"), sx, loop_y + 90, [[0, 0], [30, 0]], stroke=C["service_stroke"])
        )

    # JIT references side panel
    elements.extend(
        box_with_text(
            "jit_refs",
            1100,
            310,
            320,
            150,
            "JIT references per phase\nreasoning-engine · PE bar\nbuilding-blocks · tradeoffs\ncompany-profiles · numbers-to-know",
            fill="#f8fafc",
            stroke=C["slate"],
            dashed=True,
            tsize=12,
            tcolor=C["body"],
        )
    )
    elements.extend(
        arrow("a3", 1060, 385, [[0, 0], [35, 0]], stroke=C["slate"], dashed=True, label="loads")
    )

    # Layer 4: Interviewer + Research
    elements.extend(
        box_with_text(
            "interviewer",
            80,
            500,
            520,
            90,
            "Interviewer agent (blind review)\ncheckpoints after phases 4, 5, 6",
            fill=C["async_fill"],
            stroke=C["async_stroke"],
            tsize=14,
        )
    )
    elements.extend(
        box_with_text(
            "research",
            680,
            500,
            420,
            90,
            "Research agent\nMajor / Critical findings only",
            fill=C["async_fill"],
            stroke=C["async_stroke"],
            dashed=True,
            tsize=14,
        )
    )
    elements.extend(
        arrow("a4", 600, 545, [[0, 0], [70, 0]], stroke=C["async_stroke"], dashed=True, label="if Major+")
    )
    # Checkpoints from phase 4/5/6 down to interviewer
    elements.extend(
        arrow("a5", 755, loop_y + loop_h, [[0, 0], [0, 35]], stroke=C["async_stroke"], label="checkpoint")
    )
    elements.extend(
        arrow("a6", 905, loop_y + loop_h, [[0, 0], [0, 35], [-125, 0], [0, 0]], stroke=C["async_stroke"])
    )
    elements.extend(
        arrow("a7", 1055, loop_y + loop_h, [[0, 0], [0, 35], [-275, 0], [0, 0]], stroke=C["async_stroke"])
    )

    # Layer 5: Outer quality
    elements.extend(
        box_with_text(
            "crossfile",
            80,
            630,
            480,
            80,
            "Cross-file consistency — 5 checks",
            fill=C["decision_fill"],
            stroke=C["decision_stroke"],
            tsize=14,
        )
    )
    elements.extend(
        box_with_text(
            "pe_rubric",
            620,
            630,
            480,
            80,
            "PE rubric — 10 dimensions (avg ≥ 4.5, none < 4)",
            fill=C["decision_fill"],
            stroke=C["decision_stroke"],
            tsize=14,
        )
    )
    elements.extend(arrow("a8", 560, 670, [[0, 0], [50, 0]], stroke=C["decision_stroke"]))
    elements.extend(
        arrow("a9", 340, 590, [[0, 0], [0, 35]], stroke=C["decision_stroke"], label="after phases")
    )

    # Layer 6: Validator
    elements.extend(
        box_with_text(
            "validator",
            80,
            750,
            1020,
            80,
            "Python Validator CLI — 27 gate criteria + cross-file + quality signals + depth eval → 09-eval-report.md PASS/FAIL",
            fill=C["worker_fill"],
            stroke=C["worker_stroke"],
            tsize=14,
        )
    )
    elements.extend(
        arrow("a10", 590, 710, [[0, 0], [0, 35]], stroke=C["worker_stroke"], label="validates")
    )

    # Layer 7: Output
    elements.extend(
        box_with_text(
            "output",
            80,
            870,
            1020,
            90,
            "11 artifacts → system-design/<problem-name>/\n8 design docs + Excalidraw diagram + eval report + interview transcript",
            fill=C["store_fill"],
            stroke=C["store_stroke"],
            tsize=15,
        )
    )
    elements.extend(
        arrow("a11", 590, 830, [[0, 0], [0, 35]], stroke=C["store_stroke"], label="produces")
    )

    doc = {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {
            "viewBackgroundColor": "#ffffff",
            "gridSize": 20,
        },
        "files": {},
    }

    out = Path(__file__).with_name("architecture.excalidraw")
    out.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print(f"Wrote {out} ({len(elements)} elements)")


if __name__ == "__main__":
    main()
