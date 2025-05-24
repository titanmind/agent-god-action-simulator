from pathlib import Path

from agent_world.ai.angel import generator
from agent_world.systems.ability.ability_system import AbilitySystem


def test_generate_and_hotload(tmp_path: Path) -> None:
    world: dict = {}
    system = AbilitySystem(world)

    path = generator.generate_ability(
        "Temp ability",
        stub_code="world['val'] = world.get('val', 0) + 5",
    )
    assert path.exists()

    cls_name = generator._class_name(generator._slugify("Temp ability"))
    assert cls_name not in system.abilities

    system.update()

    assert cls_name in system.abilities
    assert system.use(cls_name, 1)
    assert world.get("val") == 5

    path.unlink()

