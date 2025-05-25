import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.time_manager import TimeManager
from agent_world.core.components.ai_state import AIState
from agent_world.core.components.role import RoleComponent
from agent_world.systems.ai.actions import ActionQueue, MoveAction
from agent_world.systems.ai.ai_reasoning_system import AIReasoningSystem, RawActionCollector
from agent_world.systems.ai.behavior_tree_system import BehaviorTreeSystem


class DummyLLM:
    mode = "live"

    def request(self, prompt: str, world: World) -> str:
        return "MOVE N"


def _setup_world() -> World:
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager()
    world.action_queue = ActionQueue()
    world.raw_actions_with_actor = RawActionCollector(world.action_queue)
    world.llm_manager_instance = DummyLLM()
    world.async_llm_responses = {}
    return world


def test_actions_enqueued_without_main_loop_transfer():
    world = _setup_world()
    ai_sys = AIReasoningSystem(world, world.llm_manager_instance, world.raw_actions_with_actor)
    bt_sys = BehaviorTreeSystem(world)

    agent_id = world.entity_manager.create_entity()
    world.component_manager.add_component(agent_id, AIState(personality="bot"))
    world.component_manager.add_component(agent_id, RoleComponent("scout", uses_llm=False))

    world.time_manager.tick_counter = 0
    bt_sys.update(0)
    ai_sys.update(0)

    # Raw list should still contain the tuple for compatibility
    assert world.raw_actions_with_actor
    actor, text = world.raw_actions_with_actor[0]
    assert actor == agent_id
    assert text.startswith("MOVE")

    # But the queue should already contain at least one parsed MoveAction
    assert len(world.action_queue) >= 1
    action = world.action_queue.pop()
    assert isinstance(action, MoveAction)
