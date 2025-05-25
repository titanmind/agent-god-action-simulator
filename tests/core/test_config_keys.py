import yaml
from pathlib import Path


def test_config_contains_new_keys():
    data = yaml.safe_load(Path("config.yaml").read_text())
    assert data["world"]["paused_for_angel_timeout_seconds"] == 60
    assert data["llm"]["agent_decision_model"] == "google/gemini-flash-1.5-8b"
    assert data["llm"]["angel_generation_model"] == "google/gemini-flash-1.5-8b"

