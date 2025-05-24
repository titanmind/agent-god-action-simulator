from typing import Any

from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.components.ai_state import AIState


def test_ai_reasoning_enqueues_actions(monkeypatch):
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()

    e1 = world.entity_manager.create_entity()
    e2 = world.entity_manager.create_entity()
    world.component_manager.add_component(e1, AIState(personality="a"))
    world.component_manager.add_component(e2, AIState(personality="b"))

    built_prompts: list[int] = []

    def dummy_build_prompt(agent_id: int, world_view: Any) -> str:
        built_prompts.append(agent_id)
        return f"prompt-{agent_id}"

    monkeypatch.setattr(
        "agent_world.ai.llm.prompt_builder.build_prompt",
        dummy_build_prompt,
        raising=False,
    )

    class DummyLLMManager:
        def __init__(self) -> None:
            self.calls: list[tuple[str, float]] = []

        def request(self, prompt: str, timeout: float) -> str:
            self.calls.append((prompt, timeout))
            return f"ACK {prompt}"

    monkeypatch.setattr(
        "agent_world.ai.llm.llm_manager.LLMManager", DummyLLMManager, raising=False
    )

    from agent_world.systems.ai.ai_reasoning_system import AIReasoningSystem

    llm = DummyLLMManager()
    actions: list[str] = []
    system = AIReasoningSystem(world, llm, actions)
    system.update(tick=1)

    assert actions == ["ACK prompt-1", "ACK prompt-2"]
    assert all(t == 0.05 for _, t in llm.calls)
    assert built_prompts == [e1, e2]
