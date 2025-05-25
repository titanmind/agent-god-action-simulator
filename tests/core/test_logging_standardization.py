import logging
from agent_world.main import bootstrap

def test_logging_standardization(caplog):
    caplog.set_level(logging.INFO)
    world = bootstrap("config.yaml")
    assert any("Angel pause timeout set" in rec.getMessage() for rec in caplog.records)

