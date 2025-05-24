from agent_world.core.entity_manager import EntityManager


def test_create_and_destroy():
    em = EntityManager()
    e1 = em.create_entity()
    e2 = em.create_entity()

    assert e1 != e2
    assert e2 == e1 + 1
    assert em.has_entity(e1)
    assert em.components(e1) == {}

    em.destroy_entity(e1)
    assert not em.has_entity(e1)

