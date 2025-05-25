import pytest
from agent_world.ai.angel import generator as angel_generator


@pytest.mark.parametrize(
    "desc",
    [
        "a simple self heal ability for 5 health",
        "disintegrate obstacle in front",
    ],
)
def test_generate_generic_stub(monkeypatch, tmp_path, desc):
    monkeypatch.setattr(angel_generator, "GENERATED_DIR", tmp_path)
    path = angel_generator.generate_ability(desc)
    text = path.read_text()

    # Generic stub should not contain previous special-case logic
    assert "from agent_world.core.components.health" not in text
    assert "OBSTACLES" not in text
    assert "is_blocked" not in text

    # Should contain the default print stub
    assert "print(f\"Agent {caster_id} used {self.__class__.__name__}" in text

