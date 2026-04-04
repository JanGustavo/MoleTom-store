import io
import os
from pathlib import Path
from uuid import uuid4
from PIL import Image, ImageFilter, ImageEnhance, ImageChops
from svg_generator import generate_svg, svg_to_image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = Path(BASE_DIR) / "static"
GENERATED_DIR = STATIC_DIR / "generated"

HOODIE_IMAGES = {
    "preto":  os.path.join(BASE_DIR, "static", "img", "moletom_preto.webp"),
    "branco": os.path.join(BASE_DIR, "static", "img", "moletom_branco.webp"),
    "vinho":  os.path.join(BASE_DIR, "static", "img", "moletom_vinho.webp"),
}

STAMP_AREA = (0.24, 0.14, 0.76, 0.60)


# -----------------------------
# REMOVE WHITE BACKGROUND
# -----------------------------
def _remove_white_background(img: Image.Image, threshold=200):

    img = img.convert("RGBA")

    new_data = []

    for r, g, b, a in img.getdata():

        if r > threshold and g > threshold and b > threshold:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append((r, g, b, a))

    img.putdata(new_data)

    return img


# -----------------------------
# AUTO CROP OBJECT
# -----------------------------
def _crop_object(img: Image.Image):

    bg = Image.new(img.mode, img.size, (0, 0, 0, 0))

    diff = ImageChops.difference(img, bg)

    bbox = diff.getbbox()

    if bbox:
        img = img.crop(bbox)

    return img


# -----------------------------
# COMPOSITION
# -----------------------------
def _composite(hoodie_path: str, stamp: Image.Image) -> str:

    hoodie = Image.open(hoodie_path).convert("RGBA")

    w, h = hoodie.size

    box_left   = int(STAMP_AREA[0] * w)
    box_top    = int(STAMP_AREA[1] * h)
    box_right  = int(STAMP_AREA[2] * w)
    box_bottom = int(STAMP_AREA[3] * h)

    box_w = box_right - box_left
    box_h = box_bottom - box_top

    # recorta objeto
    stamp = _crop_object(stamp)

    stamp_w, stamp_h = stamp.size

    # limite de tamanho
    ratio = min(box_w / stamp_w, box_h / stamp_h)

    new_w = int(stamp_w * ratio)
    new_h = int(stamp_h * ratio)

    stamp = stamp.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # leve suavização
    stamp = stamp.filter(ImageFilter.GaussianBlur(radius=0.25))

    r, g, b, a = stamp.split()

    a = ImageEnhance.Brightness(a).enhance(0.95)

    stamp = Image.merge("RGBA", (r, g, b, a))

    paste_x = box_left + (box_w - new_w) // 2
    paste_y = box_top + (box_h - new_h) // 2

    hoodie.paste(stamp, (paste_x, paste_y), mask=stamp)

    buffer = io.BytesIO()

    hoodie.convert("RGB").save(buffer, format="PNG", optimize=True)

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"design-{uuid4().hex}.png"
    file_path = GENERATED_DIR / filename
    file_path.write_bytes(buffer.getvalue())

    return f"/static/generated/{filename}"


# -----------------------------
# MAIN FUNCTION
# -----------------------------
def generate_design(prompt: str, color: str = "preto") -> str:
    normalized_prompt = (prompt or "").strip()
    if not normalized_prompt:
        raise RuntimeError("Informe um prompt para gerar a estampa.")

    color = color.lower()

    hoodie_path = HOODIE_IMAGES.get(color, HOODIE_IMAGES["preto"])

    if not os.path.exists(hoodie_path):
        raise RuntimeError("Imagem base não encontrada")

    try:
        svg_code = generate_svg(normalized_prompt, color)
        stamp = svg_to_image(svg_code)
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Falha ao gerar estampa procedural: {exc}") from exc

    return _composite(hoodie_path, stamp)


def generate_hoodie_image(prompt: str, color: str = "preto") -> str:
    return generate_design(prompt, color)