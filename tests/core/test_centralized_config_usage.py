import yaml
from pathlib import Path

from agent_world.config import load_config
from agent_world.main import bootstrap
from agent_world.persistence import event_log


def test_centralized_config_application(monkeypatch, tmp_path):
    cfg = {
        "world": {"size": [5, 5]},
        "llm": {
            "mode": "offline",
            "agent_decision_model": "agent-test-model",
            "angel_generation_model": "angel-test-model",
        },
        "paths": {
            "abilities_builtin": str(tmp_path / "builtin"),
            "abilities_generated": str(tmp_path / "generated"),
            "abilities_vault": str(tmp_path / "vault"),
        },
        "cache": {"log_retention_mb": 1},
    }

    for p in cfg["paths"].values():
        Path(p).mkdir(parents=True, exist_ok=True)

    config_file = tmp_path / "cfg.yaml"
    config_file.write_text(yaml.dump(cfg))

    custom_config = load_config(config_file)
    monkeypatch.setattr("agent_world.config.CONFIG", custom_config, raising=False)
    monkeypatch.setattr(event_log, "CONFIG", custom_config, raising=False)

    world = bootstrap(config_path=config_file)

    llm = world.llm_manager_instance
    assert llm.agent_decision_model == "agent-test-model"
    assert llm.angel_generation_model == "angel-test-model"

    ability_sys = world.ability_system_instance
    expected_dirs = [
        Path(cfg["paths"]["abilities_builtin"]),
        Path(cfg["paths"]["abilities_generated"]),
        Path(cfg["paths"]["abilities_vault"]),
    ]
    assert ability_sys.search_dirs == expected_dirs

    assert event_log._log_retention_bytes() == 1 * 1024 * 1024

