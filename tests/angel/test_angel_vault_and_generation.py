from pathlib import Path
from agent_world.core.world import World
from agent_world.core.component_manager import ComponentManager
from agent_world.ai.angel import generator as angel_generator
from agent_world.ai.angel.system import get_angel_system
from agent_world.core.components.known_abilities import KnownAbilitiesComponent


def test_vault_hit_returns_existing_ability():
    world = World((5, 5))
    world.component_manager = ComponentManager()
    system = get_angel_system(world)

    result = system.generate_and_grant(1, "simple fireball ability")
    assert result == {"status": "success", "ability_class_name": "SampleFireball"}
    comp = world.component_manager.get_component(1, KnownAbilitiesComponent)
    assert comp is not None
    assert "SampleFireball" in comp.known_class_names


def test_llm_generation_path(monkeypatch, tmp_path):
    world = World((5, 5))
    world.component_manager = ComponentManager()

    class DummyLLM:
        def request(self, prompt: str) -> str:
            dummy_called.append(prompt)
            return "echo"

    dummy_called: list[str] = []
    world.llm_manager_instance = DummyLLM()
    system = get_angel_system(world)

    def fake_generate(desc: str) -> Path:
        p = tmp_path / "gen.py"
        p.write_text(
            "from agent_world.abilities.base import Ability\n"
            "class TempAbility(Ability):\n"
            "    def energy_cost(self) -> int: return 0\n"
            "    def cooldown(self) -> int: return 1\n"
            "    def can_use(self, caster_id, world, target_id=None) -> bool: return True\n"
            "    def execute(self, caster_id, world, target_id=None) -> None: pass\n"
            "__all__ = ['TempAbility']\n",
            encoding="utf-8",
        )
        return p

    monkeypatch.setattr(angel_generator, "generate_ability", fake_generate)

    result = system.generate_and_grant(2, "new shiny ability")
    assert result == {"status": "success", "ability_class_name": "TempAbility"}
    comp = world.component_manager.get_component(2, KnownAbilitiesComponent)
    assert comp is not None
    assert "TempAbility" in comp.known_class_names
    assert dummy_called, "LLM was not called"

