from pathlib import Path
import yaml


def test_roles_yaml_schema():
    path = Path('agent_world/data/roles.yaml')
    assert path.is_file(), 'roles.yaml file missing'

    with open(path, 'r', encoding='utf-8') as fh:
        data = yaml.safe_load(fh)

    assert isinstance(data, dict)
    # required roles
    for role in ('creature', 'merchant', 'guard'):
        assert role in data

    for role_name, cfg in data.items():
        assert isinstance(cfg, dict)
        assert set(cfg.keys()) == {
            'can_request_abilities',
            'uses_llm',
            'fixed_abilities',
        }
        assert isinstance(cfg['can_request_abilities'], bool)
        assert isinstance(cfg['uses_llm'], bool)
        assert isinstance(cfg['fixed_abilities'], list)
        assert all(isinstance(a, str) for a in cfg['fixed_abilities'])
