"""Helper for writing generated ability scaffolds."""

from __future__ import annotations

from pathlib import Path
import re


GENERATED_DIR = Path(__file__).resolve().parents[2] / "abilities" / "generated"


def _slugify(text: str) -> str:
    """Return a filesystem-friendly slug for ``text``."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")
    return slug or "ability"


def _class_name(slug: str) -> str:
    """Convert ``slug`` to PascalCase class name."""
    return "".join(part.capitalize() for part in slug.split("_")) or "GeneratedAbility"


def generate_ability(desc: str, *, stub_code: str | None = None) -> Path:
    """Create a basic ability module under :mod:`abilities.generated`.

    Parameters
    ----------
    desc:
        Short description or name used to derive the module/class.

    Returns
    -------
    pathlib.Path
        Path to the created module.
    """

    slug = _slugify(desc)
    class_name = _class_name(slug)

    filename = f"{slug}.py"
    path = GENERATED_DIR / filename
    counter = 1
    while path.exists():
        filename = f"{slug}_{counter}.py"
        path = GENERATED_DIR / filename
        counter += 1

    body = "pass"
    if stub_code:
        lines = stub_code.strip().splitlines()
        body = "\n".join("        " + ln.rstrip() for ln in lines) or "pass"

    template = f'''"""Generated ability scaffold.

Description:
    {desc}
"""

from agent_world.abilities.base import Ability


class {class_name}(Ability):
    """Auto-generated ability stub."""

    def can_use(self, user, world) -> bool:
        return True

    def execute(self, user, world) -> None:
{body}

    @property
    def energy_cost(self) -> int:
        return 0

    @property
    def cooldown(self) -> float:
        return 0.0


__all__ = ["{class_name}"]
'''

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(template, encoding="utf-8")
    return path


__all__ = ["generate_ability"]
