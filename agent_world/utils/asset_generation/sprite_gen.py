"""Runtime sprite generation using :mod:`Pillow`."""

from __future__ import annotations

from pathlib import Path
import random
from typing import Dict

from PIL import Image, ImageDraw, ImageFont


SPRITE_SIZE = (32, 32)
ASSETS_DIR = Path("assets")
ASSETS_DIR.mkdir(exist_ok=True)

_SPRITE_CACHE: Dict[int, Image.Image] = {}


def _color_from_id(entity_id: int) -> tuple[int, int, int]:
    """Deterministically derive a RGB colour from ``entity_id``."""

    rnd = random.Random(entity_id)
    return rnd.randint(0, 255), rnd.randint(0, 255), rnd.randint(0, 255)


def generate_sprite(entity_id: int) -> Image.Image:
    """Create a 32×32 ``Image`` for ``entity_id``."""

    img = Image.new("RGB", SPRITE_SIZE, _color_from_id(entity_id))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    text = str(entity_id)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(
        ((SPRITE_SIZE[0] - tw) / 2, (SPRITE_SIZE[1] - th) / 2),
        text,
        fill="white",
        font=font,
    )
    return img


def get_sprite(entity_id: int) -> Image.Image:
    """Return cached sprite image for ``entity_id``."""

    sprite = _SPRITE_CACHE.get(entity_id)
    if sprite is not None:
        return sprite

    path = ASSETS_DIR / f"{entity_id}.png"
    if path.exists():
        sprite = Image.open(path)
    else:
        sprite = generate_sprite(entity_id)
        sprite.save(path, format="PNG")

    _SPRITE_CACHE[entity_id] = sprite
    return sprite


__all__ = ["generate_sprite", "get_sprite"]
