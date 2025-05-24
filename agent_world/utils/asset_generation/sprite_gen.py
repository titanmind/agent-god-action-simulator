"""Runtime sprite generation using :mod:`Pillow`."""

from __future__ import annotations

from pathlib import Path
import random
from typing import Tuple, Optional
from collections import OrderedDict

from PIL import Image, ImageDraw, ImageFont


SPRITE_SIZE = (32, 32)
ASSETS_DIR = Path("assets")
ASSETS_DIR.mkdir(exist_ok=True)

# Maximum sprites kept in RAM before older entries are evicted.
MAX_SPRITES = 10000

CacheKey = Tuple[int, Optional[Tuple[int, int, int]]]

_SPRITE_CACHE: "OrderedDict[CacheKey, Image.Image]" = OrderedDict()


def _color_from_id(entity_id: int) -> tuple[int, int, int]:
    """Deterministically derive a RGB colour from ``entity_id``."""

    rnd = random.Random(entity_id)
    return rnd.randint(0, 255), rnd.randint(0, 255), rnd.randint(0, 255)


def generate_sprite(
    entity_id: int, outline_colour: Optional[Tuple[int, int, int]] = None
) -> Image.Image:
    """Create a 32×32 ``Image`` for ``entity_id``.

    Parameters
    ----------
    entity_id:
        Unique identifier used to deterministically generate sprite colour.
    outline_colour:
        Optional RGB tuple used to draw a border around the sprite.
    """

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
    if outline_colour is not None:
        draw.rectangle(
            [(0, 0), (SPRITE_SIZE[0] - 1, SPRITE_SIZE[1] - 1)],
            outline=outline_colour,
            width=2,
        )
    return img


def get_sprite(
    entity_id: int, outline_colour: Optional[Tuple[int, int, int]] = None
) -> Image.Image:
    """Return cached sprite image for ``entity_id``.

    ``outline_colour`` specifies an optional border. Variants with different
    outlines are cached separately.
    """

    cache_key: CacheKey = (entity_id, outline_colour)
    sprite = _SPRITE_CACHE.get(cache_key)
    if sprite is not None:
        _SPRITE_CACHE.move_to_end(cache_key)
        return sprite

    if outline_colour is None:
        path = ASSETS_DIR / f"{entity_id}.png"
        if path.exists():
            sprite = Image.open(path)
        else:
            sprite = generate_sprite(entity_id)
            sprite.save(path, format="PNG")
    else:
        sprite = generate_sprite(entity_id, outline_colour)

    _SPRITE_CACHE[cache_key] = sprite
    _SPRITE_CACHE.move_to_end(cache_key)
    if len(_SPRITE_CACHE) > MAX_SPRITES:
        # Pop least-recently-used entry
        _SPRITE_CACHE.popitem(last=False)
    return sprite


__all__ = ["generate_sprite", "get_sprite"]
