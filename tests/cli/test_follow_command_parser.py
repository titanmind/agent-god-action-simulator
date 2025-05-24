from agent_world.utils.cli.command_parser import parse_command, CLICommand


def test_follow_command_parses_correctly():
    cmd = parse_command("/follow 7")
    assert isinstance(cmd, CLICommand)
    assert cmd.name == "follow"
    assert cmd.args == ["7"]
