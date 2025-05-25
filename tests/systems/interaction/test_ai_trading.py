from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agent_world.core.world import World
from agent_world.core.entity_manager import EntityManager
from agent_world.core.component_manager import ComponentManager
from agent_world.core.time_manager import TimeManager
from agent_world.core.spatial.spatial_index import SpatialGrid
from agent_world.core.components.position import Position
from agent_world.core.components.inventory import Inventory
from agent_world.core.components.ai_state import AIState, Goal
from agent_world.core.components.perception_cache import PerceptionCache
from agent_world.systems.interaction.pickup import Tag
from agent_world.systems.interaction.trading import TradingSystem
from agent_world.ai.prompt_builder import build_prompt


def _setup_world():
    world = World((5, 5))
    world.entity_manager = EntityManager()
    world.component_manager = ComponentManager()
    world.time_manager = TimeManager()
    world.spatial_index = SpatialGrid(1)
    return world


def test_prompt_exposes_trade_info_and_trade_occurs():
    world = _setup_world()
    trading = TradingSystem(world)

    em = world.entity_manager
    cm = world.component_manager

    agent_a = em.create_entity()
    agent_b = em.create_entity()
    item_a = em.create_entity()
    item_b = em.create_entity()

    cm.add_component(agent_a, AIState(personality="trader", goals=[Goal("acquire", target=item_b)]))
    cm.add_component(agent_b, AIState(personality="trader"))
    cm.add_component(agent_a, Inventory(capacity=2, items=[item_a]))
    cm.add_component(agent_b, Inventory(capacity=2, items=[item_b]))
    cm.add_component(agent_a, Position(1, 1))
    cm.add_component(agent_b, Position(1, 1))
    cm.add_component(item_a, Tag("wood"))
    cm.add_component(item_b, Tag("ore"))

    # minimal perception so they can see each other
    cm.add_component(agent_a, PerceptionCache(visible=[agent_b], last_tick=0))

    # Adjust local market so ore and wood equal value
    world.spawn_resource("ore", 0, 0)
    world.spawn_resource("ore", 0, 1)
    world.spawn_resource("ore", 1, 0)
    world.spawn_resource("wood", 2, 2)

    prompt = build_prompt(agent_a, world)
    assert "local_market_prices" in prompt
    assert "visible_trade_partners" in prompt

    trading.update()

    inv_a = cm.get_component(agent_a, Inventory)
    inv_b = cm.get_component(agent_b, Inventory)
    assert inv_a.items[0] == item_b
    assert inv_b.items[0] == item_a
