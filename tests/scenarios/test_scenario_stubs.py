from agent_world.scenarios.base_scenario import BaseScenario
from agent_world.utils.cli.command_parser import parse_command, CLICommand


def test_base_scenario_importable():
    assert BaseScenario.__name__ == "BaseScenario"


def test_scenario_command_parses_correctly():
    cmd = parse_command("/scenario default")
    assert isinstance(cmd, CLICommand)
    assert cmd.name == "scenario"
    assert cmd.args == ["default"]
