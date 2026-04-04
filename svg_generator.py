import hashlib
import io
import math
import random
import re

from PIL import Image

try:
    import cairosvg
except ImportError:
    cairosvg = None


CANVAS_SIZE = 800


def _clean_prompt(prompt: str) -> str:
    return re.sub(r"\s+", " ", (prompt or "")).strip()


def _safe_label(prompt: str, max_chars: int = 18) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9\-\s]", "", prompt.upper()).strip()
    return sanitized[:max_chars] or "STREETWEAR"


def _palette(rng: random.Random, hoodie_color: str) -> tuple[str, str, str, str, str]:
    if hoodie_color == "branco":
        palettes = [
            ("#ffffff", "#111827", "#ef4444", "#0ea5e9", "#334155"),
            ("#ffffff", "#1f2937", "#dc2626", "#0369a1", "#475569"),
            ("#ffffff", "#0f172a", "#7c3aed", "#0891b2", "#64748b"),
        ]
    elif hoodie_color == "vinho":
        palettes = [
            ("#120810", "#f8fafc", "#f59e0b", "#22d3ee", "#a1a1aa"),
            ("#1a0a10", "#f3f4f6", "#f97316", "#38bdf8", "#94a3b8"),
            ("#0d0510", "#ffffff", "#fbbf24", "#34d399", "#9ca3af"),
        ]
    else:
        palettes = [
            ("#0b1020", "#f8fafc", "#ff2bd6", "#00e5ff", "#94a3b8"),
            ("#0f172a", "#ffffff", "#fb7185", "#22d3ee", "#9ca3af"),
            ("#111827", "#e5e7eb", "#a855f7", "#06b6d4", "#6b7280"),
        ]
    return rng.choice(palettes)


def _svg_wrap(content: str) -> str:
    return (
        f'<svg width="{CANVAS_SIZE}" height="{CANVAS_SIZE}" viewBox="0 0 {CANVAS_SIZE} {CANVAS_SIZE}" '
        f'xmlns="http://www.w3.org/2000/svg">\n{content}\n</svg>'
    )


def _outlined_path(d: str, fg: str, outline: str = "#000000", fg_width: int = 6, outline_width: int = 11) -> str:
    return (
        f'<path d="{d}" stroke="{outline}" stroke-width="{outline_width}" fill="none" '
        'stroke-linecap="round" stroke-linejoin="round" />\n'
        f'<path d="{d}" stroke="{fg}" stroke-width="{fg_width}" fill="none" '
        'stroke-linecap="round" stroke-linejoin="round" />'
    )


def _select_style(prompt: str, rng: random.Random) -> str:
    lower = prompt.lower()
    if any(token in lower for token in ("dragon", "dragao", "dragão", "draco", "wyrm", "serpente")):
        return "dragon"
    if any(token in lower for token in ("cyber", "glitch", "neon", "error", "digital", "chaos")):
        return "cyberpunk"
    if any(token in lower for token in ("esports", "esport", "clan", "logo", "gaming", "guild", "team", "squad")):
        return "esports"
    if any(token in lower for token in ("japan", "japanese", "samurai", "wave", "nippon", "oni", "katana")):
        return "japanese"
    if any(token in lower for token in ("tech", "techwear", "industrial", "hud", "grid")):
        return "techwear"
    return rng.choice(["dragon", "cyberpunk", "esports", "japanese", "techwear", "minimal"])


def _background_layer() -> str:
    return '<rect x="0" y="0" width="800" height="800" fill="transparent" />'


def _dominant_shape(style: str, fg: str) -> str:
    if style == "dragon":
        return (
            f'<circle cx="400" cy="250" r="160" stroke="#000000" stroke-width="10" fill="none" opacity="0.45" />\n'
            f'  <circle cx="400" cy="250" r="160" stroke="{fg}" stroke-width="5" fill="none" opacity="0.9" />'
        )
    if style == "esports":
        pts = "400,118 650,260 560,610 240,610 150,260"
        return (
            f'<polygon points="{pts}" stroke="#000000" stroke-width="10" fill="none" stroke-linejoin="round" opacity="0.55" />\n'
            f'  <polygon points="{pts}" stroke="{fg}" stroke-width="5" fill="none" stroke-linejoin="round" opacity="0.92" />'
        )
    if style == "cyberpunk":
        pts = "400,92 645,190 645,430 400,548 155,430 155,190"
        return (
            f'<polygon points="{pts}" stroke="#000000" stroke-width="10" fill="none" opacity="0.55" />\n'
            f'  <polygon points="{pts}" stroke="{fg}" stroke-width="5" fill="none" opacity="0.9" />'
        )
    if style == "techwear":
        return (
            f'<circle cx="400" cy="250" r="152" stroke="#000000" stroke-width="10" fill="none" opacity="0.45" />\n'
            f'  <circle cx="400" cy="250" r="152" stroke="{fg}" stroke-width="4" fill="none" opacity="0.85" />'
        )
    if style == "japanese":
        return (
            f'<circle cx="400" cy="250" r="150" stroke="#000000" stroke-width="10" fill="none" opacity="0.45" />\n'
            f'  <circle cx="400" cy="250" r="150" stroke="{fg}" stroke-width="4" fill="none" opacity="0.88" />'
        )
    return (
        f'<circle cx="400" cy="250" r="146" stroke="#000000" stroke-width="10" fill="none" opacity="0.4" />\n'
        f'  <circle cx="400" cy="250" r="146" stroke="{fg}" stroke-width="4" fill="none" opacity="0.8" />'
    )


def _dragon_svg(stroke: str, accent: str) -> str:
    body = (
        "M 108 284 "
        "C 184 176, 286 168, 352 236 "
        "S 470 356, 548 270 "
        "S 668 150, 748 262"
    )
    tail = "M 108 284 C 82 296, 62 318, 42 346"
    head = (
        "M 748 262 "
        "L 784 238 "
        "L 794 262 "
        "L 784 286 "
        "L 750 278 Z"
    )
    horn = "M 780 238 L 790 204 L 802 230"
    eye = (
        f'<circle cx="782" cy="264" r="7" fill="#000000" />\n'
        f'  <circle cx="782" cy="264" r="4" fill="{accent}" />\n'
        f'  <circle cx="784" cy="263" r="1.5" fill="#ffffff" />'
    )

    spines = []
    for sx, sy in [(232, 210), (322, 196), (412, 218), (502, 210), (592, 188)]:
        spines.append(
            f'<polygon points="{sx},{sy} {sx+14},{sy-28} {sx+28},{sy}" fill="#000000" stroke="#000000" stroke-width="2" />'
        )
        spines.append(
            f'<polygon points="{sx},{sy} {sx+14},{sy-28} {sx+28},{sy}" fill="none" stroke="{accent}" stroke-width="4" />'
        )

    return (
        _outlined_path(body, fg=stroke, fg_width=8, outline_width=14)
        + "\n  "
        + _outlined_path(tail, fg=stroke, fg_width=6, outline_width=10)
        + "\n  "
        + _outlined_path(head, fg=stroke, fg_width=6, outline_width=12)
        + "\n  "
        + _outlined_path(horn, fg=stroke, fg_width=5, outline_width=9)
        + "\n  "
        + eye
        + "\n  "
        + "\n  ".join(spines)
    )


def _cyberpunk_svg(stroke: str, accent: str, neutral: str) -> str:
    lines = []
    for y in [198, 214, 230]:
        lines.append(f'<line x1="176" y1="{y}" x2="624" y2="{y}" stroke="{accent}" stroke-width="4" opacity="0.55" />')
    for y in [258, 274, 290]:
        lines.append(f'<line x1="176" y1="{y}" x2="624" y2="{y}" stroke="{stroke}" stroke-width="8" opacity="0.92" />')

    grid = []
    for x in range(184, 621, 44):
        grid.append(f'<line x1="{x}" y1="160" x2="{x}" y2="356" stroke="{neutral}" stroke-width="1" opacity="0.12" />')
    for y in range(160, 357, 18):
        grid.append(f'<line x1="180" y1="{y}" x2="620" y2="{y}" stroke="{neutral}" stroke-width="1" opacity="0.12" />')

    text = (
        f'<text x="400" y="372" text-anchor="middle" font-size="54" font-weight="800" '
        f'font-family="Orbitron, monospace" fill="{stroke}" letter-spacing="6">CYBER</text>\n'
        f'  <text x="400" y="430" text-anchor="middle" font-size="28" font-family="monospace" '
        f'fill="{accent}" letter-spacing="8">NEURAL STREET</text>'
    )

    # Um glitch mark central dominante
    glitch = (
        f'<path d="M 206 240 L 272 240 L 300 214 L 338 286 L 380 210 L 418 240 L 470 240" '
        f'stroke="#000000" stroke-width="10" fill="none" stroke-linecap="round" stroke-linejoin="round" />\n'
        f'  <path d="M 206 240 L 272 240 L 300 214 L 338 286 L 380 210 L 418 240 L 470 240" '
        f'stroke="{stroke}" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round" />'
    )

    return "\n  ".join(lines + grid) + "\n  " + glitch + "\n  " + text


def _esports_svg(stroke: str, accent: str) -> str:
    shield = "400,118 652,258 560,620 240,620 148,258"
    star = []
    cx, cy = 400, 272
    for i in range(10):
        angle = math.radians(-90 + i * 36)
        radius = 72 if i % 2 == 0 else 34
        star.append(f"{cx + int(radius * math.cos(angle))},{cy + int(radius * math.sin(angle))}")
    star_joined = " ".join(star)
    return (
        f'<polygon points="{shield}" fill="none" stroke="#000000" stroke-width="12" stroke-linejoin="round" />\n'
        f'  <polygon points="{shield}" fill="none" stroke="{stroke}" stroke-width="7" stroke-linejoin="round" />\n'
        f'  <polygon points="{star_joined}" fill="none" stroke="#000000" stroke-width="10" stroke-linejoin="round" />\n'
        f'  <polygon points="{star_joined}" fill="none" stroke="{accent}" stroke-width="5" stroke-linejoin="round" />\n'
        f'  <circle cx="{cx}" cy="{cy}" r="18" fill="none" stroke="{stroke}" stroke-width="4" />\n'
        f'  <circle cx="{cx}" cy="{cy}" r="6" fill="{stroke}" />\n'
        f'  <text x="400" y="446" text-anchor="middle" font-size="86" font-weight="800" '
        f'font-family="Impact, sans-serif" fill="{stroke}" letter-spacing="4">GG</text>'
    )


def _japanese_svg(stroke: str, accent: str) -> str:
    waves = [
        '<clipPath id="jp-clip">',
        '  <circle cx="400" cy="250" r="116" />',
        '</clipPath>',
        '<g clip-path="url(#jp-clip)">',
    ]

    radius = 40
    cols = 6
    rows = 6
    start_x = 400 - (cols // 2) * radius
    start_y = 118

    for row in range(rows):
        for col in range(cols):
            cx = start_x + col * radius + (radius // 2 if row % 2 else 0)
            cy = start_y + row * int(radius * 0.72)
            waves.append(
                f'  <path d="M {cx - radius} {cy} A {radius} {radius} 0 0 1 {cx + radius} {cy}" '
                f'stroke="#000000" stroke-width="10" fill="none" opacity="0.55" />'
            )
            waves.append(
                f'  <path d="M {cx - radius} {cy} A {radius} {radius} 0 0 1 {cx + radius} {cy}" '
                f'stroke="{stroke}" stroke-width="5" fill="none" opacity="0.96" />'
            )
            inner_r = int(radius * 0.55)
            waves.append(
                f'  <path d="M {cx - inner_r} {cy} A {inner_r} {inner_r} 0 0 1 {cx + inner_r} {cy}" '
                f'stroke="{accent}" stroke-width="2" fill="none" opacity="0.58" />'
            )

    waves.append('</g>')
    return "\n  ".join(waves)


def _techwear_svg(stroke: str, accent: str, neutral: str) -> str:
    overlay = []
    for pos in [176, 220, 264, 308, 352]:
        overlay.append(f'<line x1="{pos}" y1="150" x2="{pos}" y2="350" stroke="{neutral}" stroke-width="1" opacity="0.18" />')
    for pos in [180, 224, 268, 312, 356]:
        overlay.append(f'<line x1="180" y1="{pos}" x2="620" y2="{pos}" stroke="{neutral}" stroke-width="1" opacity="0.18" />')
    for x, y in [(214, 178), (612, 182), (206, 392), (618, 390)]:
        overlay.append(f'<polygon points="{x},{y} {x+16},{y+8} {x},{y+16}" fill="{accent}" opacity="0.72" />')
    overlay.append(f'<rect x="256" y="156" width="288" height="2" fill="{accent}" opacity="0.28" />')
    overlay.append(f'<rect x="208" y="356" width="260" height="2" fill="{accent}" opacity="0.28" />')
    overlay.append(f'<text x="172" y="146" font-size="10" fill="{neutral}" font-family="monospace" opacity="0.7">CTRL-07</text>')
    overlay.append(f'<text x="556" y="148" font-size="10" fill="{neutral}" font-family="monospace" opacity="0.7">GRID</text>')
    overlay.append(f'<text x="178" y="402" font-size="10" fill="{neutral}" font-family="monospace" opacity="0.7">NOISE</text>')

    core = (
        f'<path d="M 292 180 L 400 156 L 508 180 L 534 250 L 508 320 L 400 344 L 292 320 L 266 250 Z" '
        f'stroke="#000000" stroke-width="10" fill="none" opacity="0.45" />\n'
        f'  <path d="M 292 180 L 400 156 L 508 180 L 534 250 L 508 320 L 400 344 L 292 320 L 266 250 Z" '
        f'stroke="{stroke}" stroke-width="5" fill="none" opacity="0.92" />'
    )
    return "\n  ".join(overlay) + "\n  " + core


def _minimal_svg(label: str, stroke: str, accent: str) -> str:
    return (
        f'<circle cx="400" cy="250" r="150" stroke="#000000" stroke-width="10" fill="none" opacity="0.45" />\n'
        f'  <circle cx="400" cy="250" r="150" stroke="{stroke}" stroke-width="5" fill="none" opacity="0.9" />\n'
        f'  <text x="400" y="286" text-anchor="middle" font-size="74" font-weight="800" '
        f'font-family="monospace" fill="{stroke}" letter-spacing="5">{label}</text>\n'
        f'  <text x="400" y="340" text-anchor="middle" font-size="22" font-family="monospace" '
        f'fill="{accent}" letter-spacing="8">STREETWEAR LAB</text>'
    )


def _type_separator(color: str) -> str:
    return f'<line x1="176" y1="476" x2="624" y2="476" stroke="{color}" stroke-width="1.2" opacity="0.35" />'


def _typography_layer(label: str, base: str, accent_a: str, accent_b: str) -> str:
    n = max(len(label), 1)
    ls = 4
    fs = int((420 - (n - 1) * ls) / max(n * 0.58, 1))
    fs = max(20, min(fs, 54))
    y = 548
    return (
        f'<text x="400" y="{y}" text-anchor="middle" font-size="{fs}" font-weight="800" '
        f'fill="none" stroke="#000000" stroke-width="4" stroke-linejoin="round" '
        f'font-family="monospace" letter-spacing="{ls}">{label}</text>\n'
        f'  <text x="398" y="{y}" text-anchor="middle" font-size="{fs}" font-weight="800" '
        f'fill="{accent_b}" font-family="monospace" letter-spacing="{ls}" opacity="0.68">{label}</text>\n'
        f'  <text x="402" y="{y}" text-anchor="middle" font-size="{fs}" font-weight="800" '
        f'fill="{accent_a}" font-family="monospace" letter-spacing="{ls}" opacity="0.68">{label}</text>\n'
        f'  <text x="400" y="{y}" text-anchor="middle" font-size="{fs}" font-weight="800" '
        f'fill="{base}" font-family="monospace" letter-spacing="{ls}">{label}</text>'
    )


def _hero_svg(style: str, stroke: str, accent_a: str, accent_b: str, neutral: str, label: str) -> str:
    if style == "dragon":
        return _dragon_svg(stroke, accent_a)
    if style == "cyberpunk":
        return _cyberpunk_svg(stroke, accent_a, neutral)
    if style == "esports":
        return _esports_svg(stroke, accent_a)
    if style == "japanese":
        return _japanese_svg(stroke, accent_b)
    if style == "techwear":
        return _techwear_svg(stroke, accent_a, neutral)
    return _minimal_svg(label, stroke, accent_b)


def generate_svg(prompt: str, hoodie_color: str = "preto") -> str:
    cleaned_prompt = _clean_prompt(prompt)
    seed = int(hashlib.md5(cleaned_prompt.encode("utf-8")).hexdigest(), 16)
    rng = random.Random(seed)

    style = _select_style(cleaned_prompt, rng)
    bg, base, accent_a, accent_b, neutral = _palette(rng, hoodie_color)
    label = _safe_label(cleaned_prompt, max_chars=18)

    content = "\n  ".join(
        [
            _background_layer(),
            _dominant_shape(style, base),
            _hero_svg(style, base, accent_a, accent_b, neutral, label),
            _type_separator(base),
            _typography_layer(label, base, accent_a, accent_b),
        ]
    )

    return _svg_wrap(content)


def svg_to_image(svg_code: str) -> Image.Image:
    if cairosvg is None:
        raise RuntimeError("Dependencia cairosvg nao encontrada. Instale com: pip install cairosvg")

    png_bytes = cairosvg.svg2png(bytestring=svg_code.encode("utf-8"))
    return Image.open(io.BytesIO(png_bytes)).convert("RGBA")
