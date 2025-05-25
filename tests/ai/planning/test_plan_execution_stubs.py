from agent_world.core.components.ai_state import AIState, ActionStep


def test_ai_state_retry_and_generation_fields():
    state = AIState(personality="test")
    assert state.plan_step_retries == 0
    assert state.max_plan_step_retries == 3
    assert state.last_plan_generation_tick == -1


def test_action_step_has_optional_type():
    step = ActionStep(action="MOVE")
    assert hasattr(step, "step_type")
    assert step.step_type is None
