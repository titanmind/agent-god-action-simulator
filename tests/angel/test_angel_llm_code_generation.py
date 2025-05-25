from pathlib import Path
from agent_world.core.world import World
from agent_world.core.component_manager import ComponentManager
from agent_world.ai.angel.system import get_angel_system
from agent_world.ai.angel import generator as angel_generator


def test_llm_code_generation(monkeypatch, tmp_path):
    world = World((5, 5))
    world.component_manager = ComponentManager()

    class DummyLLM:
        def __init__(self):
            self.calls = []
            self.angel_generation_model = "angel-model"
            self.mode = "live"

        def request(self, prompt: str, *args, **kwargs) -> str:
            self.calls.append((prompt, kwargs.get("model")))
            return "print('dummy')"

    llm = DummyLLM()
    world.llm_manager_instance = llm
    system = get_angel_system(world)

    monkeypatch.setattr(
        system,
        "_build_angel_code_generation_prompt",
        lambda desc, c, s: "prompt"
    )

    captured = {}

    def fake_generate(desc: str, *, stub_code: str | None = None) -> Path:
        captured["stub"] = stub_code
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

    system.generate_and_grant(1, "custom ability")

    assert llm.calls and llm.calls[0][0] == "prompt"
    assert llm.calls[0][1] == llm.angel_generation_model
    assert captured.get("stub") == "print('dummy')"
