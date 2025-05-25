import sys
from pathlib import Path
import asyncio

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.time_manager import TimeManager
from agent_world.core.components.ai_state import AIState, ActionStep
from agent_world.systems.ai.actions import ActionQueue, MoveAction
from agent_world.systems.ai.ai_reasoning_system import AIReasoningSystem, RawActionCollector


class RecordingLLM:
    mode = "live"

    def __init__(self) -> None:
        self.last_prompt = None
        self.response = "IDLE"

    def request(self, prompt: str, world: World) -> str:
        self.last_prompt = prompt
        return self.response


def _setup_world() -> World:
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager()
    world.action_queue = ActionQueue()
    world.raw_actions_with_actor = RawActionCollector(world.action_queue)
    world.async_llm_responses = {}
    return world


def test_direct_plan_step_success_clears_retry():
    world = _setup_world()
    llm = RecordingLLM()
    world.llm_manager_instance = llm
    ai_sys = AIReasoningSystem(world, world.llm_manager_instance, world.raw_actions_with_actor)

    agent = world.entity_manager.create_entity()
    step = ActionStep(action="MOVE", parameters={"arg": "N"})
    ai_state = AIState(personality="t", current_plan=[step])
    world.component_manager.add_component(agent, ai_state)

    world.time_manager.tick_counter = 0
    ai_sys.update(0)

    assert not ai_state.current_plan
    assert ai_state.plan_step_retries == 0
    assert len(world.action_queue) == 1
    action = world.action_queue.pop()
    assert isinstance(action, MoveAction)


def test_plan_failure_exceeds_retries_triggers_replan():
    world = _setup_world()
    llm = RecordingLLM()
    world.llm_manager_instance = llm
    ai_sys = AIReasoningSystem(world, world.llm_manager_instance, world.raw_actions_with_actor)

    agent = world.entity_manager.create_entity()
    step = ActionStep(action="MOVE", parameters={"arg": "N"})
    ai_state = AIState(personality="t", current_plan=[step])
    ai_state.plan_step_retries = ai_state.max_plan_step_retries
    ai_state.last_bt_move_failed = True
    world.component_manager.add_component(agent, ai_state)

    world.time_manager.tick_counter = 1
    ai_sys.update(1)

    assert ai_state.current_plan == []
    assert ai_state.plan_step_retries == 0
    assert ai_state.last_plan_generation_tick == 1
    assert len(world.action_queue) == 0


def test_deal_with_obstacle_prompt_sent():
    world = _setup_world()
    llm = RecordingLLM()
    world.llm_manager_instance = llm
    ai_sys = AIReasoningSystem(world, world.llm_manager_instance, world.raw_actions_with_actor)

    agent = world.entity_manager.create_entity()
    step = ActionStep(action="WAIT", step_type="DEAL_WITH_OBSTACLE", parameters={"coords": (1, 1), "goal": "2,2"})
    ai_state = AIState(personality="t", current_plan=[step])
    world.component_manager.add_component(agent, ai_state)

    world.time_manager.tick_counter = 0
    ai_sys.update(0)

    assert llm.last_prompt is not None
    assert "Obstacle at (1, 1) blocks your path" in llm.last_prompt


class PendingLLM:
    mode = "live"

    def __init__(self) -> None:
        self.agent_decision_model = "test-model"
        self.prompt_id = "b" * 32

    def request(self, prompt: str, world: World) -> str:
        fut = asyncio.Future()
        # Intentionally do not set a result so the future remains pending
        world.async_llm_responses[self.prompt_id] = fut
        return self.prompt_id


def test_bt_skipped_while_waiting_for_llm():
    llm = PendingLLM()
    world = _setup_world()
    world.llm_manager_instance = llm
    ai_sys = AIReasoningSystem(world, llm, world.raw_actions_with_actor)

    agent = world.entity_manager.create_entity()
    step = ActionStep(
        action="WAIT",
        step_type="DEAL_WITH_OBSTACLE",
        parameters={"coords": (1, 1), "goal": "(2,2)"},
    )
    ai_state = AIState(personality="t", current_plan=[step])
    world.component_manager.add_component(agent, ai_state)

    world.time_manager.tick_counter = 0
    ai_sys.update(0)

    assert list(world.action_queue._queue) == []
    assert world.raw_actions_with_actor == []
    assert ai_state.pending_llm_prompt_id == llm.prompt_id
