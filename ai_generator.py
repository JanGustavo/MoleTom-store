from openai import OpenAI
import os
import base64
from pathlib import Path
from uuid import uuid4

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
STATIC_DIR = Path(__file__).resolve().parent / "static"
GENERATED_DIR = STATIC_DIR / "generated"


def _save_generated_image(image_b64):
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    image_bytes = base64.b64decode(image_b64)
    filename = f"design-{uuid4().hex}.png"
    file_path = GENERATED_DIR / filename
    file_path.write_bytes(image_bytes)
    return f"/static/generated/{filename}"

def generate_design(prompt):

    full_prompt = f"""
    minimalist streetwear hoodie print,
    vector graphic,
    centered chest design,
    {prompt}
    """

    result = client.images.generate(
        model="gpt-image-1",
        prompt=full_prompt,
        size="1024x1024"
    )

    first_image = result.data[0]

    if getattr(first_image, "url", None):
        return first_image.url

    if getattr(first_image, "b64_json", None):
        return _save_generated_image(first_image.b64_json)

    raise RuntimeError("A API de imagem não retornou url nem b64_json.")