from pathlib import Path
from agent_world.core.world import World
from agent_world.core.component_manager import ComponentManager
from agent_world.ai.angel.system import get_angel_system
from agent_world.ai.angel import generator as angel_generator
from agent_world.core.components.known_abilities import KnownAbilitiesComponent


def _setup():
    world = World((5, 5))
    world.component_manager = ComponentManager()
    system = get_angel_system(world)
    return world, system


def _write_fake_ability(path: Path) -> None:
    path.write_text(
        "from agent_world.abilities.base import Ability\n"
        "class TempAbility(Ability):\n"
        "    def energy_cost(self) -> int: return 0\n"
        "    def cooldown(self) -> int: return 1\n"
        "    def can_use(self, caster_id, world, target_id=None) -> bool: return True\n"
        "    def execute(self, caster_id, world, target_id=None) -> None: pass\n"
        "__all__ = ['TempAbility']\n",
        encoding="utf-8",
    )


def test_conceptual_testing_success(monkeypatch, tmp_path):
    world, system = _setup()

    class DummyLLM:
        def __init__(self):
            self.calls = []
            self.angel_generation_model = "angel"
            self.mode = "live"

        def request(self, prompt: str, *args, **kwargs) -> str:
            self.calls.append(prompt)
            if len(self.calls) == 1:
                return "print('ok')"
            return "PASS: looks fine"

    world.llm_manager_instance = DummyLLM()
    monkeypatch.setattr(system, "_build_angel_code_generation_prompt", lambda d, c, s: "prompt")

    captured = {}

    def fake_generate(desc: str, *, stub_code: str | None = None) -> Path:
        captured["stub"] = stub_code
        p = tmp_path / "gen.py"
        _write_fake_ability(p)
        return p

    monkeypatch.setattr(angel_generator, "generate_ability", fake_generate)

    result = system.generate_and_grant(1, "auto ability")
    assert result == {"status": "success", "ability_class_name": "TempAbility"}
    comp = world.component_manager.get_component(1, KnownAbilitiesComponent)
    assert comp and "TempAbility" in comp.known_class_names
    assert captured["stub"] == "print('ok')"
    assert len(world.llm_manager_instance.calls) == 2
    assert "auto ability" in world.llm_manager_instance.calls[1]
    assert "print('ok')" in world.llm_manager_instance.calls[1]


def test_conceptual_testing_failure(monkeypatch):
    world, system = _setup()

    class DummyLLM:
        def __init__(self):
            self.calls = []
            self.angel_generation_model = "angel"
            self.mode = "live"

        def request(self, prompt: str, *args, **kwargs) -> str:
            self.calls.append(prompt)
            if len(self.calls) == 1:
                return "print('bad')"
            return "FAIL: uses bad API"

    world.llm_manager_instance = DummyLLM()
    monkeypatch.setattr(system, "_build_angel_code_generation_prompt", lambda d, c, s: "prompt")

    called = {}

    def fake_generate(desc: str, *, stub_code: str | None = None) -> Path:
        called["called"] = True
        return Path("noop")

    monkeypatch.setattr(angel_generator, "generate_ability", fake_generate)

    result = system.generate_and_grant(2, "bad ability")
    assert result["status"] == "failure"
    assert "conceptual test failed" in result["reason"]
    assert "called" not in called
    assert len(world.llm_manager_instance.calls) == 2

