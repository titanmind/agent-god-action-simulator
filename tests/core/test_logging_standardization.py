import importlib
import logging


def test_logging_configured():
    logging.basicConfig(level=logging.WARNING, force=True)
    import agent_world.main as main
    importlib.reload(main)
    assert logging.getLogger().getEffectiveLevel() == logging.INFO
