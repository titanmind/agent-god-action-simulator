from agent_world.config import CONFIG, WorldConfig, LLMConfig


def test_config_module_loads_config():
    assert isinstance(CONFIG.world, WorldConfig)
    assert isinstance(CONFIG.llm, LLMConfig)
    assert CONFIG.world.paused_for_angel_timeout_seconds == 60
    assert CONFIG.llm.agent_decision_model == "google/gemini-flash-1.5-8b"
    assert CONFIG.llm.angel_generation_model == "google/gemini-flash-1.5-8b"

