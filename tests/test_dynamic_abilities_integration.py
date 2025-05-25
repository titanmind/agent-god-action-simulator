
# tests/test_dynamic_abilities_integration.py
import pytest
import shutil
from pathlib import Path
import time 

from agent_world.main import bootstrap
from agent_world.core.world import World
from agent_world.core.components.ai_state import AIState
from agent_world.core.components.health import Health
from agent_world.core.components.position import Position
from agent_world.systems.ai.actions import Action, LogAction, MoveAction, GenerateAbilityAction, UseAbilityAction
from agent_world.ai.angel.generator import GENERATED_DIR as ABILITIES_GENERATED_DIR, _slugify, _class_name_from_slug
from agent_world.systems.ability.ability_system import AbilitySystem


@pytest.fixture
def fresh_world_with_llm_and_ability_system(mock_openrouter_api): 
    # Clean up generated abilities before each test run
    if ABILITIES_GENERATED_DIR.exists():
        for f in ABILITIES_GENERATED_DIR.glob("*.py"):
            if f.name != "__init__.py": # Don't delete __init__.py
                f.unlink(missing_ok=True) 
    
    world = bootstrap(config_path="config.yaml") # Assumes config.yaml is in project root or accessible
    
    # Ensure AbilitySystem instance is attached to world for the test
    world.ability_system_instance = None
    for system_instance in world.systems_manager._systems:
        if isinstance(system_instance, AbilitySystem):
            world.ability_system_instance = system_instance
            break
    assert world.ability_system_instance is not None, "AbilitySystem not found in bootstrapped world"

    yield world # Provide the world to the test

    # Clean up generated abilities after test run (optional, but good practice)
    if ABILITIES_GENERATED_DIR.exists():
        for f in ABILITIES_GENERATED_DIR.glob("*.py"):
            if f.name != "__init__.py":
                f.unlink(missing_ok=True)


def test_agent_requests_generates_and_uses_heal_ability(
    fresh_world_with_llm_and_ability_system: World, 
    mock_openrouter_api, 
    capsys # For capturing stdout
):
    world = fresh_world_with_llm_and_ability_system
    
    # Setup agent
    agent_id = world.entity_manager.create_entity()
    world.component_manager.add_component(agent_id, Position(5,5))
    # Start with low health to clearly see the heal effect
    initial_health_val = 1
    max_health_val = 10
    world.component_manager.add_component(agent_id, Health(initial_health_val, max_health_val)) 
    world.component_manager.add_component(agent_id, AIState(personality="problem_solver", goals=["Heal self completely"]))
    world.spatial_index.insert(agent_id, (5,5))

    # This description MUST match the trigger in angel_generator.py
    test_ability_description = "a simple self heal ability for 5 health"
    
    expected_slug = _slugify(test_ability_description)
    expected_class_name = _class_name_from_slug(expected_slug)
    expected_filename = f"{expected_slug}.py"

    print(f"[Test Setup] Agent ID: {agent_id}, Initial Health: {initial_health_val}/{max_health_val}")
    print(f"[Test Setup] Expected slug: {expected_slug}, class: {expected_class_name}, file: {expected_filename}")

    # Mock LLM responses sequence
    # AIReasoningSystem.COOLDOWN_TICKS is 10
    mock_responses = {
        f"Agent {agent_id}": [ 
            f"LOG I am low on health ({initial_health_val}/{max_health_val}). Goal: Heal self completely. I need a healing ability.", # LLM decides this first
            f"GENERATE_ABILITY {test_ability_description}",                                           # LLM decides this after cooldown
            f"USE_ABILITY {expected_class_name}"                                                      # LLM decides this after generation, loading, and another cooldown
        ]
    }
    mock_openrouter_api.set_responses_for_agents(mock_responses)
    
    # Determine max_ticks needed
    # Tick ~0: AIState gets prompt, requests from LLM.
    # Tick ~11: LLM response 1 (LOG) arrives. Action enqueued.
    # Tick ~12: LOG action executed by ActionExecutionSystem. last_llm_action_tick set to ~11.
    # Tick ~22 (11 + 10 cooldown + 1): AIState requests again.
    # Tick ~33: LLM response 2 (GENERATE_ABILITY) arrives. Action enqueued.
    # Tick ~34: GENERATE_ABILITY action executed. .py file created. last_llm_action_tick set to ~33.
    # Tick ~35: AbilitySystem.update() loads the new .py file.
    # Tick ~44 (33 + 10 cooldown + 1): AIState requests again. Prompt should list new ability.
    # Tick ~55: LLM response 3 (USE_ABILITY) arrives. Action enqueued.
    # Tick ~56: USE_ABILITY action executed. Health should change. last_llm_action_tick set to ~55.
    max_ticks = 60 # Give some buffer

    for i in range(max_ticks):
        world.time_manager.tick_counter = i # Manually set tick for deterministic testing
        
        # AIReasoningSystem runs, potentially gets LLM response and adds to world.raw_actions_with_actor
        # ActionExecutionSystem runs, processes ActionQueue
        # AbilitySystem.update runs, loads abilities
        
        # Process raw actions into the queue (simulating part of the main loop)
        if world.raw_actions_with_actor and world.action_queue is not None:
            for actor_id_loop, action_text_loop in world.raw_actions_with_actor:
                world.action_queue.enqueue_raw(actor_id_loop, action_text_loop)
            world.raw_actions_with_actor.clear()
        elif world.raw_actions_with_actor and world.action_queue is None:
             print(f"[Test Tick {i} CRITICAL] world.action_queue is None, cannot process raw actions.") # Should not happen
            
        world.systems_manager.update(world, i) # Pass world and current tick


    # --- Assertions ---
    captured = capsys.readouterr() # Get all stdout
    
    # 1. Assert the .py file for the ability was created
    target_generated_file_path = ABILITIES_GENERATED_DIR / expected_filename
    assert target_generated_file_path.exists(), \
        (f"Expected ability file '{target_generated_file_path}' was not found. "
         f"Contents of {ABILITIES_GENERATED_DIR}: {[p.name for p in ABILITIES_GENERATED_DIR.glob('*.py') if p.name != '__init__.py']}")

    # 2. Assert the ability was loaded into AbilitySystem
    assert world.ability_system_instance is not None, "AbilitySystem instance is unexpectedly None after loop."
    assert expected_class_name in world.ability_system_instance.abilities, \
        (f"Ability '{expected_class_name}' not found in AbilitySystem. "
         f"Loaded: {list(world.ability_system_instance.abilities.keys())}")

    # 3. Assert the specific print output from the heal ability's execute method
    #    The heal amount is 5. Initial health 1, max 10. So, healed by 5 to 6.
    expected_heal_amount_applied = 5 
    expected_final_health_val = initial_health_val + expected_heal_amount_applied
    
    expected_use_log_print = f"Agent {agent_id} used {expected_class_name} and healed for {expected_heal_amount_applied} HP. Health: {expected_final_health_val}/{max_health_val}"
    assert expected_use_log_print in captured.out, \
        f"Expected USE_ABILITY print output ('{expected_use_log_print}') not found in stdout."

    # 4. Assert game state change: agent's health increased
    final_health_comp = world.component_manager.get_component(agent_id, Health)
    assert final_health_comp is not None, "Health component not found on agent at end of test."
    assert final_health_comp.cur == expected_final_health_val, \
        (f"Agent's health did not increase as expected. "
         f"Initial: {initial_health_val}, Expected Final: {expected_final_health_val}, Actual Final: {final_health_comp.cur}")

    # 5. (Optional) Assert other logged actions happened
    assert f"Agent {agent_id} LOG]: I am low on health ({initial_health_val}/{max_health_val}). Goal: Heal self completely. I need a healing ability." in captured.out, \
        "Initial LOG action message not found in output."
    assert f"[ActionExec] Agent {agent_id} requested generation of ability: '{test_ability_description}'" in captured.out, \
        "GENERATE_ABILITY action execution message not found in output."