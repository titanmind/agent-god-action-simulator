import os
from pathlib import Path

from PIL import Image

from agent_world.utils.asset_generation import sprite_gen, noise


def test_white_noise_dimensions() -> None:
    data = noise.white_noise(4, 3, seed=123)
    assert len(data) == 3
    assert all(len(row) == 4 for row in data)
    data2 = noise.white_noise(4, 3, seed=123)
    assert data == data2


def test_threshold_mask() -> None:
    values = [[0.1, 0.9], [0.5, 0.95]]
    mask = noise.threshold_mask(values, 0.8)
    assert mask == [[False, True], [False, True]]


def test_get_sprite_generates_and_caches(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(sprite_gen, "ASSETS_DIR", tmp_path)
    monkeypatch.setattr(sprite_gen, "_SPRITE_CACHE", {})

    img1 = sprite_gen.get_sprite(7)
    assert isinstance(img1, Image.Image)
    assert (tmp_path / "7.png").exists()

    img2 = sprite_gen.get_sprite(7)
    assert img1 is img2
