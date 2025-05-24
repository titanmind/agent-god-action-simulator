from pathlib import Path

from agent_world.ai.angel import generator
from agent_world.systems.ability.ability_system import AbilitySystem


def test_generate_ability_with_stub(monkeypatch, tmp_path: Path) -> None:
    gen_dir = tmp_path / "abilities" / "generated"
    monkeypatch.setattr(generator, "GENERATED_DIR", gen_dir)

    world: dict = {}
    system = AbilitySystem(world, search_dirs=[gen_dir])

    path = generator.generate_ability(
        "Test Ability", stub_code="world['flag'] = True"
    )
    assert path.exists()

    system.update()
    ability_name = generator._class_name(generator._slugify("Test Ability"))
    assert ability_name in system.abilities

    assert system.use(ability_name, 1)
    assert world.get("flag") is True
