#!/usr/bin/env python3
"""Render README architecture diagram to PNG (stdlib + Pillow)."""

from __future__ import annotations

from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as e:
    raise SystemExit(
        "Pillow required: cd assets && uv sync && uv run python render_with_pillow.py"
    ) from e

OUT = Path(__file__).with_name("architecture.png")
W, H = 1500, 1020

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
    "body": "#64748b",
    "on_light": "#374151",
    "white": "#ffffff",
    "panel": "#f8fafc",
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        p = Path(path)
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except OSError:
                continue
    return ImageFont.load_default()


def rounded_box(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    *,
    fill: str,
    outline: str,
    radius: int = 12,
    width: int = 2,
    dashed: bool = False,
) -> None:
    if dashed:
        x0, y0, x1, y1 = xy
        draw.rounded_rectangle(xy, radius=radius, outline=outline, width=width)
        draw.rectangle((x0 + 4, y0 + 4, x1 - 4, y1 - 4), fill=fill, outline=None)
    else:
        draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def multiline(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    fnt,
    fill: str,
    max_width: int,
    line_spacing: int = 6,
) -> None:
    x, y = xy
    for line in text.split("\n"):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + line_spacing


def arrow_down(draw: ImageDraw.ImageDraw, x: int, y0: int, y1: int, color: str, label: str | None = None) -> None:
    draw.line((x, y0, x, y1 - 8), fill=color, width=2)
    draw.polygon([(x, y1), (x - 6, y1 - 10), (x + 6, y1 - 10)], fill=color)
    if label:
        draw.text((x + 10, (y0 + y1) // 2 - 8), label, font=font(11), fill=C["body"])


def arrow_right(draw: ImageDraw.ImageDraw, x0: int, y: int, x1: int, color: str, label: str | None = None) -> None:
    draw.line((x0, y, x1 - 8, y), fill=color, width=2)
    draw.polygon([(x1, y), (x1 - 10, y - 6), (x1 - 10, y + 6)], fill=color)
    if label:
        draw.text(((x0 + x1) // 2 - 20, y - 18), label, font=font(11), fill=C["body"])


def main() -> None:
    img = Image.new("RGB", (W, H), C["white"])
    draw = ImageDraw.Draw(img)
    f_title = font(26, bold=True)
    f_head = font(15, bold=True)
    f_body = font(13)
    f_small = font(12)

    draw.text((W // 2 - 340, 24), "System Design Interview Skill — How It Works", font=f_title, fill=C["title"])

    # Layer 1
    rounded_box(draw, (60, 78, 340, 148), fill=C["client_fill"], outline=C["client_stroke"])
    multiline(draw, (78, 92), 'User prompt\n"Design a URL shortener"', fnt=f_body, fill=C["on_light"], max_width=240)

    rounded_box(draw, (500, 78, 1440, 148), fill=C["client_fill"], outline=C["client_stroke"])
    multiline(
        draw,
        (520, 98),
        "Any SKILL.md agent — Cursor · Claude Code · Codex · Gemini · Copilot",
        fnt=f_body,
        fill=C["on_light"],
        max_width=900,
    )
    arrow_right(draw, 350, 113, 490, C["client_stroke"], "activates")

    # Layer 2
    rounded_box(draw, (60, 178, 480, 258), fill=C["service_fill"], outline=C["service_stroke"])
    multiline(draw, (78, 196), "SKILL.md metadata (~100 tokens)\n→ full skill on trigger", fnt=f_body, fill=C["on_light"], max_width=380)

    rounded_box(draw, (540, 178, 1440, 258), fill=C["service_fill"], outline=C["service_stroke"])
    multiline(draw, (558, 198), "orchestrator.md — 6-phase generate → evaluate → fix loop", fnt=f_body, fill=C["on_light"], max_width=860)
    arrow_right(draw, 490, 218, 530, C["service_stroke"])

    # Layer 3: phase loop
    rounded_box(draw, (60, 288, 1040, 448), fill=C["service_fill"], outline=C["service_stroke"])
    draw.text((78, 302), "6-Phase Inner Loop — generate → evaluate → fix (max 2× per gate)", font=f_head, fill=C["service_stroke"])

    phases = ["1\nReq", "2\nNFR", "3\nAPI", "Context\ncheckpoint", "4\nHLD", "5\nDive", "6\nTrade"]
    xs = [90, 230, 370, 510, 650, 790, 930]
    for label, x in zip(phases, xs):
        if "checkpoint" in label:
            multiline(draw, (x, 360), label, fnt=f_small, fill=C["body"], max_width=110)
        else:
            rounded_box(draw, (x, 350, x + 100, 420), fill=C["white"], outline=C["service_stroke"])
            multiline(draw, (x + 28, 365), label, fnt=f_body, fill=C["on_light"], max_width=80)
    for x in [190, 330, 470, 610, 750, 890]:
        arrow_right(draw, x + 100, 385, x + 130, C["service_stroke"])

    rounded_box(draw, (1080, 288, 1440, 448), fill=C["panel"], outline=C["body"], dashed=True)
    multiline(
        draw,
        (1098, 312),
        "JIT references per phase\nreasoning-engine · PE bar\nbuilding-blocks · tradeoffs\ncompany-profiles · numbers-to-know",
        fnt=f_small,
        fill=C["body"],
        max_width=320,
    )
    arrow_right(draw, 1045, 368, 1075, C["body"], "loads")

    # Layer 4
    rounded_box(draw, (60, 478, 580, 568), fill=C["async_fill"], outline=C["async_stroke"])
    multiline(draw, (78, 498), "Interviewer agent (blind review)\ncheckpoints after phases 4, 5, 6", fnt=f_body, fill=C["on_light"], max_width=480)

    rounded_box(draw, (660, 478, 1100, 568), fill=C["async_fill"], outline=C["async_stroke"], dashed=True)
    multiline(draw, (678, 498), "Research agent\nMajor / Critical findings only", fnt=f_body, fill=C["on_light"], max_width=400)
    arrow_right(draw, 590, 523, 650, C["async_stroke"], "if Major+")
    arrow_down(draw, 760, 448, 472, C["async_stroke"], "checkpoint")

    # Layer 5
    rounded_box(draw, (60, 598, 520, 678), fill=C["decision_fill"], outline=C["decision_stroke"])
    multiline(draw, (78, 622), "Cross-file consistency — 5 checks", fnt=f_body, fill=C["on_light"], max_width=420)

    rounded_box(draw, (600, 598, 1100, 678), fill=C["decision_fill"], outline=C["decision_stroke"])
    multiline(draw, (618, 618), "PE rubric — 10 dimensions (avg ≥ 4.5, none < 4)", fnt=f_body, fill=C["on_light"], max_width=460)
    arrow_right(draw, 530, 638, 590, C["decision_stroke"])
    arrow_down(draw, 320, 568, 592, C["decision_stroke"], "after phases")

    # Layer 6
    rounded_box(draw, (60, 708, 1100, 788), fill=C["worker_fill"], outline=C["worker_stroke"])
    multiline(
        draw,
        (78, 728),
        "Python Validator CLI — 27 gate criteria + cross-file + quality signals + depth eval → 09-eval-report.md PASS/FAIL",
        fnt=f_body,
        fill=C["on_light"],
        max_width=1020,
    )
    arrow_down(draw, 580, 678, 702, C["worker_stroke"], "validates")

    # Layer 7
    rounded_box(draw, (60, 818, 1100, 908), fill=C["store_fill"], outline=C["store_stroke"])
    multiline(
        draw,
        (78, 838),
        "11 artifacts → system-design/<problem-name>/\n8 design docs + Excalidraw diagram + eval report + interview transcript",
        fnt=f_body,
        fill=C["on_light"],
        max_width=1020,
    )
    arrow_down(draw, 580, 788, 812, C["store_stroke"], "produces")

    img.save(OUT, format="PNG", optimize=True)
    print(OUT)


if __name__ == "__main__":
    main()
