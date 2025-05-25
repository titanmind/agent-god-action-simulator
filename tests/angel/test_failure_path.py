from agent_world.core.world import World
from agent_world.core.component_manager import ComponentManager
from agent_world.ai.angel import generator as angel_generator
from agent_world.ai.angel.system import get_angel_system
from agent_world.core.components.ai_state import AIState


def test_generation_failure_sets_error(monkeypatch):
    world = World((5, 5))
    world.component_manager = ComponentManager()
    system = get_angel_system(world)

    agent_id = 1
    world.component_manager.add_component(agent_id, AIState(personality="tester"))

    def fail_generate(desc: str):
        raise RuntimeError("boom")

    monkeypatch.setattr(angel_generator, "generate_ability", fail_generate)

    result = system.generate_and_grant(agent_id, "broken ability")
    ai_state = world.component_manager.get_component(agent_id, AIState)
    assert result == {"status": "failure", "reason": "boom"}
    assert ai_state.last_error == "boom"
    assert ai_state.needs_immediate_rethink is True
