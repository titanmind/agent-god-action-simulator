import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.time_manager import TimeManager
from agent_world.core.components.position import Position
from agent_world.core.components.health import Health
from agent_world.core.components.known_abilities import KnownAbilitiesComponent
from agent_world.systems.ai.actions import ActionQueue, UseAbilityAction
from agent_world.systems.ai.action_execution_system import ActionExecutionSystem
from agent_world.systems.ability.ability_system import AbilitySystem
from agent_world.systems.combat.combat_system import CombatSystem


def test_use_denied_without_known_ability(monkeypatch):
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager()
    queue = ActionQueue()
    combat = CombatSystem(world)
    ability_system = AbilitySystem(world)
    world.ability_system_instance = ability_system
    system = ActionExecutionSystem(world, queue, combat)

    actor = world.entity_manager.create_entity()
    target = world.entity_manager.create_entity()

    world.component_manager.add_component(actor, Position(0, 0))
    world.component_manager.add_component(target, Position(1, 0))
    world.component_manager.add_component(target, Health(cur=10, max=10))
    # Intentionally do not grant the ability
    world.component_manager.add_component(actor, KnownAbilitiesComponent([]))

    called = {}

    def stub_use(name: str, caster: int, target_id: int | None = None) -> bool:
        called["used"] = True
        return True

    monkeypatch.setattr(ability_system, "use", stub_use)

    queue._queue.append(UseAbilityAction(actor=actor, ability_name="MeleeStrike", target_id=target))
    system.update(0)

    assert "used" not in called
