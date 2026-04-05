import io
import os
import base64
import urllib.parse
import urllib.request
from pathlib import Path
from uuid import uuid4
from PIL import Image, ImageFilter, ImageEnhance, ImageChops

import requests
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = Path(BASE_DIR) / "static"
GENERATED_DIR = STATIC_DIR / "generated"

HOODIE_IMAGES = {
    "preto":  os.path.join(BASE_DIR, "static", "img", "moletom_preto.webp"),
    "branco": os.path.join(BASE_DIR, "static", "img", "moletom_branco.webp"),
    "vinho":  os.path.join(BASE_DIR, "static", "img", "moletom_vinho.webp"),
}

# Área do peito do moletom (left, top, right, bottom) em proporção 0.0–1.0
STAMP_AREA = (0.24, 0.14, 0.76, 0.60)

# Endpoint Pollinations — gratuito, sem token
POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?width=768&height=768&model=flux&nologo=true&enhance=true"


# -----------------------------
# GERAÇÃO DA ESTAMPA VIA IA
# -----------------------------
def _generate_stamp(prompt: str) -> Image.Image:
    """
    Chama Pollinations.ai (FLUX, gratuito, sem auth) para gerar a arte da estampa.
    Prompt otimizado para retornar só a arte, sem moletom no resultado.
    """
    stamp_prompt = (
        f"2D sticker art, isolated on white background: {prompt}. "
        f"Bold outline, vibrant colors, flat vector illustration. "
        f"No clothing, no hoodie, no fabric, no person. Only the graphic artwork."
    )

    encoded = urllib.parse.quote(stamp_prompt)
    url = POLLINATIONS_URL.format(prompt=encoded)

    req = urllib.request.Request(url, headers={"User-Agent": "MoleTom-Store/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Pollinations retornou status {resp.status}")
        data = resp.read()

    return Image.open(io.BytesIO(data)).convert("RGBA")


# -----------------------------
# REMOVE FUNDO BRANCO
# -----------------------------
def _remove_white_background(img: Image.Image, threshold: int = 220) -> Image.Image:
    img = img.convert("RGBA")
    new_data = [
        (r, g, b, 0) if r > threshold and g > threshold and b > threshold else (r, g, b, a)
        for r, g, b, a in img.getdata()
    ]
    img.putdata(new_data)
    return img


# -----------------------------
# AUTO CROP DO OBJETO
# -----------------------------
def _crop_object(img: Image.Image) -> Image.Image:
    bg = Image.new(img.mode, img.size, (0, 0, 0, 0))
    diff = ImageChops.difference(img, bg)
    bbox = diff.getbbox()
    if bbox:
        img = img.crop(bbox)
    return img


# -----------------------------
# COMPOSIÇÃO NO MOLETOM
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

    stamp = _crop_object(stamp)
    stamp_w, stamp_h = stamp.size
    ratio = min(box_w / stamp_w, box_h / stamp_h)
    new_w = int(stamp_w * ratio)
    new_h = int(stamp_h * ratio)

    stamp = stamp.resize((new_w, new_h), Image.Resampling.LANCZOS)
    stamp = stamp.filter(ImageFilter.GaussianBlur(radius=0.25))

    r, g, b, a = stamp.split()
    a = ImageEnhance.Brightness(a).enhance(0.95)
    stamp = Image.merge("RGBA", (r, g, b, a))

    paste_x = box_left + (box_w - new_w) // 2
    paste_y = box_top  + (box_h - new_h) // 2

    hoodie.paste(stamp, (paste_x, paste_y), mask=stamp)

    buffer = io.BytesIO()
    hoodie.convert("RGB").save(buffer, format="PNG", optimize=True)

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"design-{uuid4().hex}.png"
    file_path = GENERATED_DIR / filename
    with open(file_path, "wb") as output_file:
        output_file.write(buffer.getvalue())

    url_da_nuvem = _upload_to_imgbb(file_path)

    try:
        file_path.unlink()
    except OSError:
        pass

    return url_da_nuvem


# -----------------------------
# FUNÇÃO PRINCIPAL
# -----------------------------
def generate_design(prompt: str, color: str = "preto") -> str:
    normalized_prompt = (prompt or "").strip()
    if not normalized_prompt:
        raise RuntimeError("Informe um prompt para gerar a estampa.")

    color = color.lower()
    hoodie_path = HOODIE_IMAGES.get(color, HOODIE_IMAGES["preto"])

    if not os.path.exists(hoodie_path):
        raise RuntimeError(f"Imagem base não encontrada: {hoodie_path}")

    try:
        stamp = _generate_stamp(normalized_prompt)
    except Exception as exc:
        raise RuntimeError(f"Falha ao gerar estampa: {exc}") from exc

    stamp = _remove_white_background(stamp)
    return _composite(hoodie_path, stamp)


def generate_hoodie_image(prompt: str, color: str = "preto") -> str:
    return generate_design(prompt, color)


def _upload_to_imgbb(image_path: Path) -> str:
    api_key = os.environ.get("IMGBB_API_KEY")
    if not api_key:
        raise RuntimeError("IMGBB_API_KEY nao configurada.")

    with open(image_path, "rb") as file:
        payload = {
            "key": api_key,
            "image": base64.b64encode(file.read()).decode("utf-8"),
        }

    resposta = requests.post("https://api.imgbb.com/1/upload", data=payload, timeout=60)
    if resposta.status_code != 200:
        raise RuntimeError("Falha ao hospedar a imagem na nuvem.")

    data = resposta.json()
    if not data.get("success"):
        raise RuntimeError("Falha ao hospedar a imagem na nuvem.")

    return data["data"]["url"]