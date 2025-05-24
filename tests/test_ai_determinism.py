import types

from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.spatial.spatial_index import SpatialGrid
from agent_world.core.components.position import Position
from agent_world.core.components.ai_state import AIState
from agent_world.core.components.health import Health
from agent_world.core.components.physics import Physics
from agent_world.systems.ai.actions import ActionQueue, parse_action
from agent_world.systems.movement.physics_system import PhysicsSystem, Force as PhysForce
from agent_world.systems.movement.movement_system import MovementSystem
from agent_world.systems.combat.combat_system import CombatSystem
from agent_world.ai.llm.llm_manager import LLMManager


def _make_world() -> World:
    w = World((5, 5))
    w.entity_manager = EntityManager()
    w.component_manager = ComponentManager()
    w.spatial_index = SpatialGrid(cell_size=1)
    return w


def test_llm_integration_one_tick(mock_llm, monkeypatch):
    world = _make_world()
    em = world.entity_manager
    cm = world.component_manager

    a1 = em.create_entity()
    a2 = em.create_entity()

    cm.add_component(a1, AIState(personality="a"))
    cm.add_component(a2, AIState(personality="b"))
    cm.add_component(a1, Position(1, 1))
    cm.add_component(a2, Position(1, 2))
    cm.add_component(a1, Physics(mass=1.0, vx=0.0, vy=0.0, friction=1.0))
    cm.add_component(a2, Physics(mass=1.0, vx=0.0, vy=0.0, friction=1.0))
    cm.add_component(a1, Health(cur=20, max=20))

    world.spatial_index.insert(a1, (1, 1))
    world.spatial_index.insert(a2, (1, 2))

    # Simplify prompt building
    import importlib, sys
    ai_reasoning_system = importlib.import_module(
        "agent_world.systems.ai.ai_reasoning_system"
    )
    AIReasoningSystem = ai_reasoning_system.AIReasoningSystem
    ActionExecutionSystem = importlib.import_module(
        "agent_world.systems.ai.action_execution_system"
    ).ActionExecutionSystem

    orig_prompt = ai_reasoning_system.build_prompt
    ai_reasoning_system.build_prompt = lambda aid, w: f"Agent {aid}"

    # Use physics-system Force for movement
    def patched_apply_force(world, eid, dx, dy, ttl=1):
        cm = world.component_manager
        existing = cm.get_component(eid, PhysForce)
        if existing is None:
            cm.add_component(eid, PhysForce(dx, dy))
        else:
            existing.fx += dx
            existing.fy += dy

    monkeypatch.setattr(
        "agent_world.core.components.force.apply_force", patched_apply_force
    )
    monkeypatch.setattr(
        "agent_world.systems.ai.action_execution_system.apply_force",
        patched_apply_force,
    )

    mock_llm({a1: "MOVE N", a2: f"ATTACK {a1}"})

    llm = LLMManager()
    raw_actions: list[str] = []
    ai = AIReasoningSystem(world, llm, raw_actions)
    actions = ActionQueue()
    combat = CombatSystem(world)
    executor = ActionExecutionSystem(world, actions, combat)
    phys = PhysicsSystem(world)
    movement = MovementSystem(world)

    ai.update(tick=1)
    for eid, text in zip([a1, a2], raw_actions):
        actions.enqueue_raw(eid, text)

    executor.update(tick=1)
    phys.update()
    movement.update()

    pos = cm.get_component(a1, Position)
    hp = cm.get_component(a1, Health)

    assert (pos.x, pos.y) == (1, 0)
    assert hp.cur == 10

    # restore prompt builder and unload module for subsequent tests
    ai_reasoning_system.build_prompt = orig_prompt
    sys.modules.pop("agent_world.systems.ai.ai_reasoning_system", None)
