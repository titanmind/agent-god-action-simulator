import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.time_manager import TimeManager
from agent_world.core.spatial.spatial_index import SpatialGrid
from agent_world.utils.cli import commands
from agent_world.systems.ai.actions import ActionQueue
from agent_world.systems.ai.ai_reasoning_system import AIReasoningSystem, RawActionCollector
from agent_world.systems.ai.behavior_tree_system import BehaviorTreeSystem
from agent_world.ai.behaviors.generic_bt import build_resource_gather_tree


class DummyQueue(ActionQueue):
    def __bool__(self) -> bool:
        return True


class DummyLLM:
    def __init__(self, response: str = "MOVE N"):
        self.mode = "live"
        self.prompts: list[str] = []
        self.response = response
        self.agent_decision_model = "test-model"

    def request(self, prompt: str, world: World, *, model: str | None = None) -> str:
        self.prompts.append(prompt)
        return self.response


def _setup_world(llm: DummyLLM | None = None) -> World:
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager()
    world.spatial_index = SpatialGrid(1)
    world.action_queue = DummyQueue()
    world.raw_actions_with_actor = RawActionCollector(world.action_queue)
    world.llm_manager_instance = llm or DummyLLM()
    world.async_llm_responses = {}
    return world


ROLES_TEXT = """trader:\n  can_request_abilities: false\n  uses_llm: true\n  fixed_abilities:\n    - TradeAbility\ncrafter:\n  can_request_abilities: true\n  uses_llm: true\n  fixed_abilities:\n    - CraftItem\nscavenger:\n  can_request_abilities: false\n  uses_llm: false\n  fixed_abilities:\n    - HarvestAbility\n"""


def test_scavenger_behavior_tree(monkeypatch, tmp_path):
    world = _setup_world()
    roles_yaml = tmp_path / "roles.yaml"
    roles_yaml.write_text(ROLES_TEXT, encoding="utf-8")
    monkeypatch.setattr(commands, "ROLES_PATH", roles_yaml)

    scavenger = commands.spawn(world, "npc:scavenger", "0", "0")
    bt_sys = BehaviorTreeSystem(world)
    bt_sys.register_tree("scavenger", build_resource_gather_tree())

    world.time_manager.tick_counter = 0
    bt_sys.update(0)

    assert len(world.action_queue) > 0
    action = world.action_queue.pop()
    assert action.actor == scavenger
    assert type(action).__name__ in {"MoveAction", "HarvestAction"}


def test_trader_llm_plan(monkeypatch, tmp_path):
    llm = DummyLLM()
    world = _setup_world(llm)
    roles_yaml = tmp_path / "roles.yaml"
    roles_yaml.write_text(ROLES_TEXT, encoding="utf-8")
    monkeypatch.setattr(commands, "ROLES_PATH", roles_yaml)

    trader = commands.spawn(world, "npc:trader")
    ai_sys = AIReasoningSystem(world, llm, world.raw_actions_with_actor)

    world.time_manager.tick_counter = 0
    ai_sys.update(0)

    assert llm.prompts
    assert "trade" in llm.prompts[0].lower()
    assert len(world.action_queue) > 0


def test_crafter_llm_plan(monkeypatch, tmp_path):
    llm = DummyLLM()
    world = _setup_world(llm)
    roles_yaml = tmp_path / "roles.yaml"
    roles_yaml.write_text(ROLES_TEXT, encoding="utf-8")
    monkeypatch.setattr(commands, "ROLES_PATH", roles_yaml)

    crafter = commands.spawn(world, "npc:crafter")
    ai_sys = AIReasoningSystem(world, llm, world.raw_actions_with_actor)

    world.time_manager.tick_counter = 0
    ai_sys.update(0)

    assert llm.prompts
    assert "craft" in llm.prompts[0].lower()
    assert len(world.action_queue) > 0
