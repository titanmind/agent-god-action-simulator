## Phase 1 · Foundational Stubs & Global Flags

Lay the scaffolding components, global flags, and directory placeholders needed by later phases without changing runtime behaviour.

### Wave 1-S  (stub — merge first)

Task 1-S-1
Developer @dev-alice
Files allowed:
└─ agent\_world/core/components/known\_abilities.py
└─ tests/core/test\_known\_abilities\_stub.py
Outline:
• create `KnownAbilitiesComponent` dataclass with `known_class_names: list[str] = field(default_factory=list)`
• register import in components **init**.py and serializer stub
• add basic test for default state

Task 1-S-2
Developer @dev-bob
Files allowed:
└─ agent\_world/core/components/role.py
└─ tests/core/test\_role\_stub.py
Outline:
• create `RoleComponent` dataclass with `role_name`, `can_request_abilities: bool = True`, `uses_llm: bool = True`, `fixed_abilities: list[str] = field(default_factory=list)`
• hook into serializer
• unit-test field persistence

Task 1-S-3
Developer @dev-carol
Files allowed:
└─ agent\_world/core/world.py
└─ agent\_world/core/components/ai\_state.py
└─ tests/core/test\_world\_pause\_flag.py
Outline:
• add `self.paused_for_angel: bool = False` to `World.__init__`
• extend `AIState` with `needs_immediate_rethink: bool = False`
• verify defaults via test

Task 1-S-4
Developer @dev-dave
Files allowed:
└─ agent\_world/abilities/vault/**init**.py
Outline:
• create empty package to mark new vault directory

### Wave 1-A  (parallel once Wave 1-S merged)

Task 1-A-1
Developer @dev-ellen
Files allowed:
└─ agent\_world/main.py
└─ tests/integration/test\_world\_pause.py
Outline:
• update main loop to skip `systems_manager.update` & `time_manager.sleep_until_next_tick` when `world.paused_for_angel` is True
• test confirms tick counter frozen while flag set

Task 1-A-2
Developer @dev-frank
Files allowed:
└─ agent\_world/systems/ai/action\_execution\_system.py
└─ tests/systems/test\_generate\_ability\_pause.py
Outline:
• on `GenerateAbilityAction` set `world.paused_for_angel = True` before Angel call and back to False after return/exception
• test verifies flag toggling around stub Angel execution

### Wave 1-B  (stub)

Task 1-B-1
Developer @dev-alice
Files allowed:
└─ AGENTS.md
└─ tests/conftest.py
└─ tests/shims/dotenv.py
└─ tests/integration/test_*.py
Outline:
• Create tests/shims/dotenv.py with FakeLoader stub
• Add pytest_configure() in conftest to register "integration" marker
• Decorate every integration / LLM test with @pytest.mark.integration or @skip_offline
• Remove duplicate sentence + typo in AGENTS.md

## Phase 2 · Angel System Framework

Introduce a modular AngelSystem with vault lookup and stubbed LLM generation, replacing direct template writes.

### Wave 2-S  (stub — merge first)

Task 2-S-1
Developer @dev-grace
Files allowed:
└─ agent\_world/ai/angel/system.py
└─ tests/angel/test\_angel\_system\_stub.py
Outline:
• create `class AngelSystem:` with `generate_and_grant(agent_id:int, description:str) -> dict` returning `{"status":"stub"}`
• store instance on `world` via helper `get_angel_system(world)`
• basic stub test

Task 2-S-2
Developer @dev-heidi
Files allowed:
└─ agent\_world/systems/ai/action\_execution\_system.py
Outline:
• replace direct `angel_generator.generate_ability` call with `world.get_angel_system().generate_and_grant(...)`
• keep behaviour unchanged for stub phase

### Wave 2-A  (serial – touches AngelSystem)

Task 2-A-1
Developer @dev-heidi
Files allowed:
└─ agent\_world/ai/angel/system.py
└─ agent\_world/ai/angel/vault\_index.py
└─ agent\_world/abilities/vault/sample\_fireball.py
└─ tests/angel/test\_angel\_vault\_and\_generation.py
Outline:
• scan `abilities/vault/` modules for `METADATA = {"tags":[…],"description":…}` and build simple keyword index
• if request description matches vault entry ➜ return `{"status":"success","ability_class_name":…}`
• else invoke `world.llm_manager_instance.request` (echo/offline) with coding prompt, write file via existing `angel_generator.generate_ability` helper, capture class name
• append granted class to `KnownAbilitiesComponent` (create if absent)
• unit tests cover vault hit, LLM path, component update

## Phase 3 · Immediate Agent Re-evaluation

Enable the requesting agent to act again instantly after an Angel grant.

### Wave 3-A  (parallel)

Task 3-A-1
Developer @dev-ivan
Files allowed:
└─ agent\_world/ai/angel/system.py
Outline:
• after successful grant set `ai_state.needs_immediate_rethink = True` for the agent

Task 3-A-2
Developer @dev-alice
Files allowed:
└─ agent\_world/systems/ai/ai\_reasoning\_system.py
└─ tests/systems/test\_immediate\_rethink.py
Outline:
• at start of per-agent loop, if `needs_immediate_rethink` is True: clear flag and bypass cooldown check this tick

## Phase 4 · Role-Based NPCs & Spawn Overhaul

Introduce roles, fixed abilities, and LLM/Angel gating.

### Wave 4-A  (parallel)

Task 4-A-1
Developer @dev-bob
Files allowed:
└─ agent\_world/data/roles.yaml
└─ tests/data/test\_roles\_yaml.py
Outline:
• define YAML schema `role_name: {can_request_abilities:bool, uses_llm:bool, fixed_abilities:[…]}`
• sample roles: creature, merchant, guard

Task 4-A-2
Developer @dev-carol
Files allowed:
└─ agent\_world/utils/cli/commands.py
└─ tests/cli/test\_spawn\_roles.py
Outline:
• extend `/spawn` to accept role string, load from roles.yaml
• attach `RoleComponent` and populate `KnownAbilitiesComponent` with `fixed_abilities`

Task 4-A-3
Developer @dev-dave
Files allowed:
└─ agent\_world/systems/ai/ai\_reasoning\_system.py
└─ tests/systems/test\_role\_gating.py
Outline:
• if `RoleComponent.uses_llm` is False skip LLM path, delegate to behaviour tree
• when building prompt, suppress `GENERATE_ABILITY` if `can_request_abilities` is False

Task 4-A-4
Developer @dev-ellen
Files allowed:
└─ agent\_world/ai/prompt\_builder.py
└─ tests/ai/test\_prompt\_role\_options.py
Outline:
• hide “GENERATE\_ABILITY” line and ability list when role forbids them
• ensure prompt still compiles for default agents

### Wave 4-B  (serial follow-up)

Task 4-B-1
Developer @dev-frank
Files allowed:
└─ agent\_world/ai/behaviors/creature\_bt.py
└─ agent\_world/systems/ai/behavior\_tree\_system.py
└─ tests/ai/test\_creature\_bt.py
Outline:
• add simple wander/attack behaviour tree for `creature` role
• hook into `BehaviorTreeSystem` dispatch by role

## Phase 5 · Player Removal & Camera Follow

Eliminate hard-coded player entity and add GUI follow helpers.

### Wave 5-S  (stub — merge first)

Task 5-S-1
Developer @dev-grace
Files allowed:
└─ agent\_world/gui/renderer.py
└─ tests/gui/test\_renderer\_stub.py
Outline:
• add stub `center_on_entity(entity_id:int)` that no-ops for now; test import

### Wave 5-A  (parallel)

Task 5-A-1
Developer @dev-heidi
Files allowed:
└─ agent\_world/main.py
└─ tests/integration/test\_no\_player\_bootstrap.py
Outline:
• remove PLAYER\_ID creation logic in `bootstrap()`
• adjust initial camera centering to world centre only
• test world boots with zero entities

Task 5-A-2
Developer @dev-ivan
Files allowed:
└─ agent\_world/utils/cli/commands.py
└─ agent\_world/gui/renderer.py
└─ tests/gui/test\_follow\_entity.py
Outline:
• add `/follow <entity_id>` CLI command that calls `renderer.center_on_entity` each tick
• implement actual centering logic in renderer; unit test via off-screen surface


## Phase 5.5 · Integration Glue

Make the already-landed features actually run in-game before we begin Phase 6.

### Wave 5.5-A

Task 5.5-A-1
Developer @dev-alice
Files allowed:
└─ agent\_world/main.py
└─ agent\_world/systems/ai/behavior\_tree\_system.py
Outline:
• instantiate `behavior_tree_system = BehaviorTreeSystem(world)` inside **bootstrap** after movement system registration
• `behavior_tree_system.register_tree("creature", build_creature_tree())`
• `sm.register(behavior_tree_system)` and set `world.behavior_tree_system_instance = behavior_tree_system`
• after creating `ability_sys`, set `world.ability_system_instance = ability_sys` if attribute missing

Task 5.5-A-2
Developer @dev-bob
Files allowed:
└─ tests/integration/test\_behavior\_tree\_integration.py
Outline:
• bootstrap a 5 × 5 world, spawn `npc:creature` at (1,1) plus dummy target at (2,1) with Health
• advance one system tick; assert `world.raw_actions_with_actor` has an entry for the creature and action starts with `"USE_ABILITY"` or `"MOVE"`
• assert any instance in `world.systems_manager._systems` is `BehaviorTreeSystem`

Task 5.5-A-3
Developer @dev-carol
Files allowed:
└─ agent\_world/utils/cli/command\_parser.py
└─ tests/cli/test\_follow\_command\_parser.py
Outline:
• add `/follow` to command parser so it forwards `name="follow", args=[entity_id]` to `commands.execute`
• unit-test parsing of string `"/follow 7"` returns expected Command object

Task 5.5-A-4
Developer @dev-dave
Files allowed:
└─ agent\_world/abilities/builtin/melee\_strike.py (create if absent)
└─ tests/abilities/test\_melee\_strike\_exists.py
Outline:
• ensure a minimal `MeleeStrike` Ability subclass (cooldown 1, melee range check) lives in builtin directory
• test `AbilitySystem(world).abilities` contains `"MeleeStrike"` after load


## Phase 6 · Observational Learning

Make ability usage perceivable and expose it to agent prompts.

### Wave 6-S  (stub — merge first)

Task 6-S-1
Developer @dev-alice
Files allowed:
└─ agent\_world/core/events.py
└─ tests/core/test\_events\_stub.py
Outline:
• add `AbilityUseEvent` dataclass (caster\_id, ability\_name, target\_id, tick)

Task 6-S-2
Developer @dev-bob
Files allowed:
└─ agent\_world/core/components/event\_log.py
Outline:
• create `EventLog` component with `recent: list[AbilityUseEvent]`

### Wave 6-A  (parallel)

Task 6-A-1
Developer @dev-carol
Files allowed:
└─ agent\_world/systems/ability/ability\_system.py
└─ tests/systems/test\_event\_emission.py
Outline:
• on successful `use`, emit `AbilityUseEvent` and append to global queue

Task 6-A-2
Developer @dev-dave
Files allowed:
└─ agent\_world/systems/ai/perception\_system.py
└─ tests/systems/test\_perception\_events.py
Outline:
• distribute events to nearby agents’ `PerceptionCache` and `EventLog`

Task 6-A-3
Developer @dev-ellen
Files allowed:
└─ agent\_world/ai/prompt\_builder.py
└─ tests/ai/test\_prompt\_recent\_events.py
Outline:
• add “RECENT EVENTS” section listing observed `ability_name`s and actors

## Phase 7 · Angel Failure Feedback

Provide structured feedback when ability generation fails.

### Wave 7-A  (serial – touches AngelSystem & prompt)

Task 7-A-1
Developer @dev-frank
Files allowed:
└─ agent\_world/ai/angel/system.py
└─ agent\_world/core/components/ai_state.py
└─ tests/angel/test\_failure\_path.py
Outline:
• on failure return `{"status":"failure","reason":…}`; write reason to `ai_state.last_error` and set `needs_immediate_rethink`

Task 7-A-2
Developer @dev-grace
Files allowed:
└─ agent\_world/ai/prompt\_builder.py
└─ tests/ai/test\_prompt\_failure\_feedback.py
Outline:
• if `ai_state.last_error` present, prepend “SYSTEM NOTE: <reason>” to prompt so agent can react

This phased, stub-first plan respects the Dev-Plan Authoring Guide v4, keeps concurrent tasks file-isolated, and incrementally evolves the codebase from its current state to the fully featured target architecture without merge-conflict pain.


## Phase 8 · Foundational Fixes & PDD Alignment

Implement critical bug fixes, align existing components and configurations more closely with the Project Design Document, and enhance core systems for better stability and future replayability.

### Wave 8-S (stub — merge first)

Task 8-S-1
Developer @dev-alice
Files allowed:
└─ agent_world/core/components/perception_cache.py
└─ agent_world/core/events.py
└─ tests/core/test_perception_cache_stubs.py
Outline:
• Add `visible_ability_uses: list[AbilityUseEvent] = field(default_factory=list)` to `PerceptionCacheComponent` dataclass.
• Ensure `AbilityUseEvent` is accessible for type hinting.
• Add basic unit test for the new field's default state in `PerceptionCacheComponent`.

Task 8-S-2
Developer @dev-bob
Files allowed:
└─ config.yaml
└─ agent_world/main.py
└─ tests/core/test_config_keys.py
Outline:
• Add new keys to `config.yaml` as per PDD Sec 12:
  ```yaml
  world:
    # ... existing ...
    paused_for_angel_timeout_seconds: 60

  llm:
    # ... existing ...
    agent_decision_model: "google/gemini-flash-1.5-8b"     # Placeholder, actual model ID can vary
    angel_generation_model: "google/gemini-flash-1.5-8b"   # Placeholder

  # paths: # Uncomment if paths section is created
    # abilities_vault: "./agent_world/abilities/vault" # Actual path
    # abilities_generated: "./agent_world/abilities/generated"
    # abilities_builtin: "./agent_world/abilities/builtin"
  ```
• Ensure `main.py` bootstrap function can gracefully handle these new keys if present (e.g., log them or store on world if appropriate) but doesn't crash if they are used by other systems not yet updated.
• Add test to verify `config.yaml` can be loaded and new keys are present with default/expected values.

Task 8-S-3
Developer @dev-carol
Files allowed:
└─ agent_world/main.py
└─ agent_world/core/world.py
└─ tests/core/test_world_system_instances.py
Outline:
• In `bootstrap()` in `main.py`, ensure `world.combat_system_instance` is set after `CombatSystem` is created and registered.
• Add a `combat_system_instance: Optional[CombatSystem] = None` field to `World` class for type hinting.
• Add test to verify `world.combat_system_instance` is populated after bootstrap.

### Wave 8-A (parallel once Wave 8-S merged)

Task 8-A-1
Developer @dev-dave
Files allowed:
└─ agent_world/abilities/builtin/melee_strike.py
└─ agent_world/abilities/builtin/ranged.py
└─ tests/abilities/test_combat_system_singleton_use.py
Outline:
• Modify `MeleeStrike.execute` and `ArrowShot.execute` to use `world.combat_system_instance.attack(...)` instead of instantiating `CombatSystem(world)`.
• Ensure `ArrowShot` finds `CombatSystem` via `world.combat_system_instance` or iterates `SystemsManager` to find it and then uses that single instance.
• Add/update tests to ensure `CombatSystem` is not re-instantiated within ability execution and that attacks still function correctly.

Task 8-A-2
Developer @dev-ellen
Files allowed:
└─ agent_world/systems/ai/perception_system.py
└─ tests/systems/test_perception_events.py
Outline:
• Modify `EventPerceptionSystem.update` (in `agent_world/systems/ai/perception_system.py`) to populate the new `visible_ability_uses` field in `PerceptionCacheComponent` for agents that can perceive an `AbilityUseEvent`.
• This is in *addition* to populating the `EventLog` component.
• Update `test_perception_events.py` to verify `PerceptionCacheComponent.visible_ability_uses` is correctly populated.

Task 8-A-3
Developer @dev-frank
Files allowed:
└─ agent_world/ai/llm/llm_manager.py
└─ agent_world/ai/angel/system.py
└─ agent_world/persistence/event_log.py
└─ tests/persistence/test_llm_angel_event_logging.py
Outline:
• Modify `LLMManager.process_queue_item` to log full LLM prompts and raw responses using `agent_world.persistence.event_log.append_event` to a world-accessible event log (e.g., `world.persistent_event_log_path`). Create this path/mechanism if it doesn't exist.
• Modify `AngelSystem.generate_and_grant` to log its key decisions (Vault hit, LLM generation attempt, success/failure, ability granted) using `append_event`.
• Define new event types (e.g., "LLM_REQUEST", "LLM_RESPONSE", "ANGEL_ACTION") for these logs.
• Add tests to verify these events are correctly logged.

Task 8-A-4
Developer @dev-grace
Files allowed:
└─ agent_world/main.py
└─ agent_world/ai/llm/llm_manager.py
└─ agent_world/systems/ability/ability_system.py
└─ agent_world/core/world.py
└─ tests/core/test_config_integration.py
Outline:
• Update `LLMManager` to utilize `llm.agent_decision_model` and `llm.angel_generation_model` from `config.yaml` (read via world or directly). Store them as distinct attributes.
• If `paths.abilities_vault` (etc.) are defined in `config.yaml`, update `AbilitySystem` to respect these paths. Default to current hardcoded paths if config keys are missing.
• The `paused_for_angel_timeout_seconds` config could be read by `main.py` loop and potentially used to break a pause if Angel system takes too long (logging a warning). This is a simple check for now.
• Add integration tests to verify that LLMManager uses different models if configured and AbilitySystem loads from configured paths.

Task 8-A-5
Developer @dev-heidi
Files allowed:
└─ agent_world/ai/angel/generator.py
└─ tests/angel/test_generic_ability_stubs.py
Outline:
• Refactor `angel_generator.generate_ability` to remove hardcoded `specific_heal_desc_trigger` and "disintegrate obstacle" logic.
• The `stub_code` parameter (if provided by AngelSystem's LLM in the future) or a default generic placeholder should be used.
• The current sophisticated hardcoded stub logic for "disintegrate obstacle" (checking `is_blocked`, `OBSTACLES.discard`) should be removed; the generated ability should be a simpler print statement or a no-op pass, relying on the LLM to generate more complex code if requested.
• Test that generating abilities with descriptions previously triggering special stubs now results in a generic stub.

### Wave 8-B (serial follow-ups after Wave 8-A)

Task 8-B-1
Developer @dev-ivan
Files allowed:
└─ agent_world/ai/prompt_builder.py
└─ tests/ai/test_prompt_visible_ability_uses.py
Outline:
• Modify `agent_world/ai/prompt_builder.build_prompt` (the one in `agent_world/ai/prompt_builder.py`).
• If `PerceptionCacheComponent.visible_ability_uses` is now the PDD-aligned source for observed abilities (rather than or in addition to `EventLog.recent`), update the prompt builder to read from it.
• If `EventLog.recent` remains the primary source for "RECENT EVENTS", this task is a no-op for `prompt_builder.py` but the test should confirm the "RECENT EVENTS" section still works correctly with the changes in `EventPerceptionSystem`.
• Add/update tests to verify the prompt includes information about observed ability uses, sourced appropriately.

Task 8-B-2
Developer @dev-alice
Files allowed:
└─ tests/integration/test_full_loop_pdd_alignment.py
Outline:
• Create a new integration test that verifies several of Phase 8's fixes/alignments working together.
• For example: an agent uses an ability, another agent perceives it (verifying `PerceptionCacheComponent.visible_ability_uses` and `EventLog` are populated), this perception influences the observing agent's next LLM decision (logged via new event logging), and `config.yaml` settings are respected.
• This test asserts key PDD-aligned behaviors post-Phase 8.



## Phase 9 · Code Cleanup & Architectural Refinements

Address remaining inconsistencies, improve code quality by refactoring hardcoded elements and standardizing logging, and refine system integrations to better align with the PDD's architectural vision. This phase prepares the codebase for advanced feature development.

### Wave 9-S (stub — merge first)

Task 9-S-1
Developer @dev-alice
Files allowed:
└─ agent_world/config.py
└─ tests/core/test_config_module.py
Outline:
• Transform `agent_world/config.py` from a placeholder into a module that loads `config.yaml` at startup.
• Define a simple dataclass or typed dictionary structure within `config.py` to hold parsed configuration values (e.g., `WorldConfig`, `LLMConfig`).
• Add basic test to ensure `config.py` loads `config.yaml` and makes values accessible. (Actual usage by other modules will be in Wave 9-A).

Task 9-S-2
Developer @dev-bob
Files allowed:
└─ agent_world/ai/angel/system.py
└─ agent_world/core/systems_manager.py
└─ tests/angel/test_angel_system_registration_stub.py
Outline:
• Add a placeholder `update(self, world: Any, tick: int) -> None:` method to `AngelSystem`.
• Add a placeholder `process_pending_requests(self) -> None:` method to `AngelSystem`.
• Add basic test to ensure `AngelSystem` can be instantiated and registered with `SystemsManager` without error (actual system logic in 9-A).

Task 9-S-3
Developer @dev-carol
Files allowed:
└─ agent_world/scenarios/__init__.py
└─ agent_world/scenarios/base_scenario.py
└─ agent_world/utils/cli/commands.py
└─ tests/scenarios/test_scenario_stubs.py
Outline:
• Create `agent_world/scenarios/` directory and `__init__.py`.
• Create `agent_world/scenarios/base_scenario.py` with an abstract `BaseScenario` class:
    ```python
    from abc import ABC, abstractmethod
    from typing import Any
    class BaseScenario(ABC):
        @abstractmethod
        def setup(self, world: Any) -> None: pass
        @abstractmethod
        def get_name(self) -> str: pass
    ```
• Add a stub for a `/scenario <name>` CLI command in `commands.py` (parsing only for now).
• Test that `BaseScenario` can be imported.

### Wave 9-A (parallel once Wave 9-S merged)

Task 9-A-1
Developer @dev-dave
Files allowed:
└─ agent_world/main.py
└─ agent_world/scenarios/default_pickup_scenario.py
└─ agent_world/utils/cli/commands.py
└─ tests/scenarios/test_pickup_scenario_command.py
Outline:
• Create `agent_world/scenarios/default_pickup_scenario.py` implementing `BaseScenario`.
• Move the current hardcoded "SCENARIO FOR ABILITY GENERATION & PICKUP" logic from `main.py` into this new `DefaultPickupScenario.setup()` method.
• Modify `main.py` to call `DefaultPickupScenario().setup(world)` by default if no scenario is specified via CLI.
• Implement the `/scenario <name>` CLI command in `commands.py` to load and run scenarios from `agent_world/scenarios/` (for now, just support "default_pickup").
• Test that the default scenario still runs and the `/scenario default_pickup` command works.

Task 9-A-2
Developer @dev-ellen
Files allowed:
└─ agent_world/main.py
└─ agent_world/ai/llm/llm_manager.py
└─ agent_world/systems/ability/ability_system.py
└─ agent_world/persistence/event_log.py
└─ agent_world/config.py
└─ tests/core/test_centralized_config_usage.py
Outline:
• Refactor `main.py` bootstrap, `LLMManager`, `AbilitySystem`, and `persistence.event_log._log_retention_bytes` to import and use the centralized `agent_world.config` module/objects for accessing configuration values instead of loading `config.yaml` directly.
• Test that configurations (e.g., LLM models, ability paths, log retention) are correctly applied from the centralized config.

Task 9-A-3
Developer @dev-frank
Files allowed:
└─ agent_world/ai/angel/system.py
└─ agent_world/systems/ai/action_execution_system.py
└─ agent_world/main.py
└─ tests/angel/test_angel_system_integration.py
Outline:
• Modify `AngelSystem` to be a proper system: register it with `SystemsManager` in `main.py::bootstrap`.
• Implement `AngelSystem.update()`: This method will likely be empty or handle internal state updates if any; for now, it can be a no-op.
• Implement `AngelSystem.process_pending_requests()`: This method will contain the core logic currently in `generate_and_grant`, potentially managing an internal queue of generation requests. For now, it can be a stub.
• Modify `main.py` loop: if `world.paused_for_angel` is True, call `world.angel_system_instance.process_pending_requests()` instead of the current direct call from `ActionExecutionSystem`.
• Modify `ActionExecutionSystem`: instead of directly calling `get_angel_system().generate_and_grant()`, it should now enqueue a request to the `AngelSystem` (e.g. add to an internal queue on `AngelSystem` instance or emit an event for `AngelSystem` to pick up). For this task, a simple direct call to a new method like `angel_system.queue_request(actor, description)` is sufficient.
• Test that `AngelSystem` is registered and `paused_for_angel` logic in `main.py` correctly calls `process_pending_requests` (even if it's a stub). Test that `GenerateAbilityAction` correctly queues a request with the AngelSystem.

Task 9-A-4
Developer @dev-grace
Files allowed:
└─ agent_world/systems/ai/actions.py
└─ agent_world/ai/llm/prompt_builder.py
└─ agent_world/utils/cli/commands.py
└─ tests/core/test_player_id_removal.py
Outline:
• Remove the `PLAYER_ID = 0` constant from `systems/ai/actions.py`.
• Remove the line `Player (ID {PLAYER_ID}) is controlled by a human.` from `ai/llm/prompt_builder.py`.
• Remove the logic in `utils/cli/commands.py::spawn()` that ensures `PLAYER_ID` has components.
• Ensure tests still pass or are updated to reflect no specific player entity. Focus on AI agent interactions.

Task 9-A-5
Developer @dev-heidi
Files allowed:
└─ agent_world/main.py
└─ agent_world/ai/llm/llm_manager.py
└─ agent_world/ai/llm/prompt_builder.py
└─ agent_world/systems/movement/physics_system.py
└─ agent_world/systems/ability/ability_system.py
└─ agent_world/systems/ability/builtin/ranged.py
└─ agent_world/systems/ai/action_execution_system.py
└─ agent_world/systems/ai/angel/generator.py
└─ agent_world/systems/ai/behavior_tree.py
└─ agent_world/utils/cli/commands.py
└─ tests/core/test_logging_standardization.py
Outline:
• Systematically replace debug `print()` statements in the listed files (and any other critical paths identified) with `logging.info()`, `logging.debug()`, or `logging.warning()` as appropriate.
• Configure basic logging in `main.py` (e.g., `logging.basicConfig(level=logging.INFO)`).
• Ensure tests still pass and critical information is now logged via the `logging` module. The very verbose debug prints in `prompt_builder` or `LLMManager` should become `logging.debug()`.

Task 9-A-6
Developer @dev-ivan
Files allowed:
└─ agent_world/systems/ai/ai_reasoning_system.py
└─ agent_world/main.py
└─ tests/systems/ai/test_action_flow_streamlining.py
Outline:
• Evaluate the `world.raw_actions_with_actor` and `world.action_queue` flow.
• If a simplification is straightforward (e.g., `AIReasoningSystem` and `BehaviorTreeSystem` directly enqueue to `world.action_queue`), implement it.
• If not, document the rationale for the current two-step process. For this task, a primary goal is to ensure `AIReasoningSystem` and `BehaviorTreeSystem` directly add parsed `Action` objects (not raw strings) to the `ActionQueue`. The `world.raw_actions_with_actor` list can be removed if actions are parsed within these AI systems before queueing.
• Update `main.py` loop to remove the transfer from `raw_actions_with_actor` to `action_queue` if it's now direct.
• Test the action processing flow.

Task 9-A-7
Developer @dev-bob
Files allowed:
└─ agent_world/main.py
└─ agent_world/systems/combat/combat_system.py
└─ agent_world/systems/interaction/crafting.py
└─ agent_world/persistence/event_log.py
└─ tests/persistence/test_unified_event_logging.py
Outline:
• Modify `CombatSystem` and `CraftingSystem` to use `agent_world.persistence.event_log.append_event` to log their significant events (e.g., attacks, deaths, crafts) to the world's persistent event log (`world.persistent_event_log_path`) instead of their local `event_log` lists.
• Remove the local `event_log` lists from these systems and their initialization in `main.py`.
• Ensure event data structures are consistent and useful for replay.
• Test that combat and crafting events are now written to the persistent log.

### Wave 9-B (serial follow-ups after Wave 9-A)

Task 9-B-1
Developer @dev-carol
Files allowed:
└─ agent_world/ai/llm/prompt_builder.py
└─ tests/ai/test_generalized_prompting.py
Outline:
• Begin refactoring the "CRITICAL SITUATION" logic in `agent_world/ai/llm/prompt_builder.py`.
• Identify the core elements of the critical advice (obstacle detection, goal item visibility) and make the advice generation less tied to the specific coordinates/IDs of the `DefaultPickupScenario`.
• The goal is not to fully generalize all AI yet, but to make this specific prompt section more adaptable if scenario parameters change.
• Test that prompts are still generated correctly for the default scenario and that critical advice adapts if key elements (like obstacle position) are programmatically changed.

Task 9-B-2
Developer @dev-alice
Files allowed:
└─ PROJECT_DESIGN.md
Outline:
• Update `PROJECT_DESIGN.md` based on the changes from Phases 8 and 9. Specifically:
    • Reflect the `PerceptionCacheComponent.visible_ability_uses` field.
    • Update `config.yaml` skeleton (Sec 12) with all newly added keys.
    • Clarify AngelSystem's integration pattern if it's now registered with `SystemsManager`.
    • Note the shift to centralized `config.py`.
    • Update event logging section to reflect unified persistent logging.
    • Clarify the role of `RestrictedPython` if its non-use for Angel's conceptual testing is now the clear state.
    • Remove any mentions of `PLAYER_ID`.
    - Identify any other items in the code that do not align with the design as well, and update them

This Phase 9 aims to significantly improve the codebase's health, align it more closely with the PDD where appropriate at this stage, and prepare it for the more complex feature work required to fully realize the "vFuture" vision.


## Phase 10 · True Angel System: LLM-Powered Ability Generation

Implement the core PDD vision for the Angel System where its LLM genuinely generates Python code for novel abilities, moving beyond predefined templates or simple stubs.

### Wave 10-S (stub — merge first)

Task 10-S-1
Developer @dev-alice
Files allowed:
└─ agent_world/ai/angel/system.py
└─ agent_world/ai/angel/templates.py
└─ tests/angel/test_angel_prompting_stubs.py
Outline:
• Add `_build_angel_code_generation_prompt(description: str, world_constraints: dict, code_scaffolds: dict) -> str` method stub to `AngelSystem`.
• Add placeholder functions in `agent_world/ai/angel/templates.py` for `get_world_constraints_for_angel()` and `get_code_scaffolds_for_angel()`, returning empty dicts.
• Test that `_build_angel_code_generation_prompt` can be called with stubbed constraint/scaffold data.

Task 10-S-2
Developer @dev-bob
Files allowed:
└─ agent_world/ai/angel/system.py
└─ agent_world/utils/sandbox.py
└─ tests/angel/test_angel_conceptual_test_stub.py
Outline:
• Add `_conceptual_test_generated_code(generated_code: str, original_request: str) -> bool` method stub to `AngelSystem`, returning `True`.
• Ensure `utils/sandbox.py` (especially `run_in_sandbox`) is importable by `AngelSystem` (no functional changes to sandbox itself yet).
• Test that `_conceptual_test_generated_code` can be called.

### Wave 10-A (parallel once Wave 10-S merged)

Task 10-A-1
Developer @dev-carol
Files allowed:
└─ agent_world/ai/angel/system.py
└─ agent_world/ai/angel/templates.py
└─ agent_world/core/world.py (read-only for context)
└─ tests/angel/test_angel_prompt_building.py
Outline:
• Implement `get_world_constraints_for_angel()` in `templates.py` to extract relevant world state (e.g., key component types, existing ability patterns, API limits) for the Angel LLM.
• Implement `get_code_scaffolds_for_angel()` in `templates.py` to provide basic ability class structure, import statements, and placeholder method signatures.
• Implement `_build_angel_code_generation_prompt` in `AngelSystem` to construct a detailed prompt for the Angel's LLM using the description, constraints, and scaffolds.
• Test various scenarios to ensure the prompt includes necessary contextual information.

Task 10-A-2
Developer @dev-dave
Files allowed:
└─ agent_world/ai/angel/system.py
└─ agent_world/ai/angel/generator.py
└─ agent_world/ai/llm/llm_manager.py
└─ tests/angel/test_angel_llm_code_generation.py
Outline:
• Modify `AngelSystem.generate_and_grant` (or its new equivalent in `process_pending_requests`):
    • When no vault match, call `_build_angel_code_generation_prompt`.
    • Use `world.llm_manager_instance.request` with the `angel_generation_model` to get Python code from the Angel's LLM.
    • Pass this LLM-generated code string to `angel_generator.generate_ability` via the `stub_code` parameter.
• Ensure `LLMManager.request` can select the `angel_generation_model` (already supported via config).
• Test that the Angel System attempts to use its LLM for code generation and that `generate_ability` receives the code. Mock LLM to return a simple valid ability string.

### Wave 10-B (serial follow-up)

Task 10-B-1
Developer @dev-ellen
Files allowed:
└─ agent_world/ai/angel/system.py
└─ agent_world/utils/sandbox.py (if needed for advanced conceptual testing later, but primarily for reasoning prompt)
└─ tests/angel/test_angel_conceptual_testing_flow.py
Outline:
• Implement the *first part* of "Conceptual Sandboxed Testing" in `AngelSystem`.
• After receiving code from the Angel LLM, before writing the file, call `_conceptual_test_generated_code`.
• For this task, `_conceptual_test_generated_code` will prompt the *same* Angel LLM (or a dedicated one if easily swappable) with the generated code and the original request, asking it to "reason about potential issues, API misuse, or if it meets the functional goal" without actually executing it in the sandbox.
• If the LLM's reasoning output indicates high confidence/no issues, proceed to grant. If issues, log them and potentially return failure (or attempt a修正 prompt).
• `utils/sandbox.py::run_in_sandbox` is NOT used to execute the ability code itself here.
• Test the flow: ability description -> LLM code gen -> LLM conceptual reasoning -> grant/fail. Mock LLM reasoning responses.

## Phase 11 · Generalized AI & Emergent Behavior Foundations

Decouple AI decision-making from hardcoded scenarios and build foundational capabilities for agents to pursue goals more emergently.

### Wave 11-S (stub — merge first)

Task 11-S-1
Developer @dev-frank
Files allowed:
└─ agent_world/core/components/ai_state.py
└─ agent_world/ai/planning/__init__.py
└─ agent_world/ai/planning/base_planner.py
└─ tests/ai/planning/test_planner_stubs.py
Outline:
• Enhance `AIStateComponent` to include richer goal representation (e.g., `goals: list[GoalObject]` where `GoalObject` might have type, target, conditions) and a `current_plan: list[ActionStep]` field.
• Create `agent_world/ai/planning/` directory and `__init__.py`.
• Create `agent_world/ai/planning/base_planner.py` with an abstract `BasePlanner` class having a `create_plan(agent_id: int, goals: list[GoalObject], world: Any) -> list[ActionStep]` method.

### Wave 11-A (parallel once Wave 11-S merged)

Task 11-A-1
Developer @dev-grace
Files allowed:
└─ agent_world/ai/llm/prompt_builder.py
└─ tests/ai/test_generalized_prompting_phase11.py
Outline:
• Completely refactor `agent_world/ai/llm/prompt_builder.build_prompt` (the non-critical one) to remove all remaining scenario-specific "CRITICAL SITUATION" / "DefaultPickupScenario" logic.
• The prompt should now be built based on the agent's generalized `AIState` (including new goal representation), perception cache, known abilities, and role, without hardcoded advice for specific scenarios.
• Focus on providing the LLM with raw, relevant information for general decision-making.
• Test that prompts are generated based on various AIStates and world conditions without specific scenario triggers.

Task 11-A-2
Developer @dev-heidi
Files allowed:
└─ agent_world/ai/planning/llm_planner.py
└─ agent_world/systems/ai/ai_reasoning_system.py
└─ tests/ai/planning/test_llm_planner.py
Outline:
• Implement `LLMPlanner(BasePlanner)` in `agent_world/ai/planning/llm_planner.py`.
• Its `create_plan` method will use the LLM (agent_decision_model) to break down high-level `AIState.goals` into a sequence of `ActionStep`s (which could be game actions or sub-goals).
• Modify `AIReasoningSystem` to:
    • If an agent has goals but no `current_plan`, invoke the `LLMPlanner` to generate one and store it in `AIState`.
    • If a plan exists, use the next step in the plan to guide the LLM prompt for the *specific action* for that step, or directly convert `ActionStep` to an `Action` if possible.
• Test that the `LLMPlanner` can generate a plan from goals and `AIReasoningSystem` attempts to follow it.

Task 11-A-3
Developer @dev-ivan
Files allowed:
└─ agent_world/ai/behaviors/
└─ tests/ai/test_expanded_behavior_trees.py
Outline:
• Expand the Behavior Tree library (`agent_world/ai/behaviors/`) with more sophisticated generic fallback nodes/trees.
• Examples: BT for resource gathering (find resource, move to it, "harvest" action), BT for fleeing if low health, BT for basic item interaction.
• These BTs should be usable by `BehaviorTreeSystem` for agents not using LLMs or when LLM/planning fails.
• Test new BT functionalities.


## Phase 11.5 · AI Core Problem-Solving & Planner Refinement

Enhance the agent's ability to recognize and plan for obstacles, trigger ability generation when necessary, and more robustly execute plans to achieve goals.

### Wave 11.5-S (stub — merge first)

Task 11.5-S-1
Developer @dev-alice
Files allowed:
└─ agent_world/core/components/ai_state.py
└─ agent_world/ai/planning/base_planner.py
└─ tests/ai/planning/test_plan_execution_stubs.py
Outline:
• In `AIStateComponent`, add `plan_step_retries: int = 0` and `max_plan_step_retries: int = 3`.
• In `AIStateComponent`, add `last_plan_generation_tick: int = -1`.
• In `base_planner.py`, modify `ActionStep` if needed to include an optional `step_type: str` (e.g., "move", "interact", "generate_ability_for_obstacle"). This is a minor stub change; full usage is in 11.5-A.
• Add basic tests for new `AIState` fields.

### Wave 11.5-A (parallel once Wave 11.5-S merged)

Task 11.5-A-1
Developer @dev-bob
Files allowed:
└─ agent_world/ai/planning/llm_planner.py
└─ agent_world/ai/llm/prompt_builder.py (for planner-specific prompt helper, if any)
└─ tests/ai/planning/test_llm_planner_obstacle_awareness.py
Outline:
• Refine `LLMPlanner.create_plan`:
    • Modify the prompt sent to the LLM to explicitly consider obstacles. It should request the LLM to include steps like "DEAL_WITH_OBSTACLE <obstacle_coords>" or "GENERATE_ABILITY 'description to remove obstacle at X,Y'" if a path to a goal target is perceived as blocked.
    • Ensure `_parse_plan_text` correctly parses these new `ActionStep` types (using `step_type` if added in 11.5-S-1).
• Test that the `LLMPlanner` generates plans that include obstacle-addressing steps when an agent's goal is clearly blocked by a known obstacle in the world state provided to the planner's prompt.

Task 11.5-A-2
Developer @dev-carol
Files allowed:
└─ agent_world/systems/ai/ai_reasoning_system.py
└─ tests/systems/ai/test_ai_reasoning_plan_execution.py
Outline:
• Enhance `AIReasoningSystem.update` to more robustly handle `ai_comp.current_plan`:
    • If an `ActionStep` is of type "DEAL_WITH_OBSTACLE" or "GENERATE_ABILITY_FOR_OBSTACLE", the system should formulate a specific prompt to the agent's decision LLM focused on *how* to deal with that obstacle (e.g., "Obstacle at X,Y blocks your path to Z. How do you proceed? Consider using/generating an ability.").
    • If an action taken (from LLM or direct plan step) fails to change relevant state (e.g., agent tries to move but position doesn't change due to blockage, or `GENERATE_ABILITY` returns failure), increment `ai_comp.plan_step_retries`.
    • If `plan_step_retries` exceeds `max_plan_step_retries`, clear `current_plan` and `plan_step_retries` to trigger a full replan in the next reasoning cycle (set `last_plan_generation_tick` to current tick to avoid immediate re-planning if planner also fails).
• Test various plan execution scenarios, including successful steps, retries, and plan failure leading to replan trigger.

Task 11.5-A-3
Developer @dev-dave
Files allowed:
└─ agent_world/ai/llm/prompt_builder.py (the one in `agent_world/ai/llm/`)
└─ tests/ai/test_prompt_builder_obstacle_context.py
Outline:
• Modify `agent_world/ai/llm/prompt_builder.build_prompt` to improve how obstacle information is presented to the agent's decision LLM when *not* executing a specific "DEAL_WITH_OBSTACLE" plan step (i.e., for general decision making).
• If an agent has an active goal and its immediate path towards the goal's target (if applicable) is blocked by an obstacle from `pathfinding.OBSTACLES`, include a clear "SYSTEM NOTE: Your direct path to current goal target <target_id/coords> is blocked by an obstacle at <obstacle_coords>. Consider alternative actions or abilities."
• This is a more generalized version of the old "CRITICAL SITUATION" logic, but presented as contextual information rather than a forced action list.
• Test that this note appears in the prompt under appropriate conditions.

Task 11.5-A-4
Developer @dev-ellen
Files allowed:
└─ agent_world/systems/ai/ai_reasoning_system.py
└─ agent_world/core/components/ai_state.py
└─ tests/systems/ai/test_generate_ability_trigger.py
Outline:
• In `AIReasoningSystem`, if an agent decides (via LLM response to general prompt or a specific "DEAL_WITH_OBSTACLE" plan step) to use `GENERATE_ABILITY`, ensure the description provided to the Angel system is reasonably contextualized if the LLM only gives a vague description.
    *   For example, if LLM says "GENERATE_ABILITY remove obstacle" and the system knows an obstacle at (X,Y) is blocking the current goal, augment the description to something like "remove obstacle at (X,Y) blocking path to goal Z".
• This task focuses on the *triggering* and *description formulation* for `GENERATE_ABILITY`, not the generation itself.
• Test that agents correctly decide to generate abilities for obstacles and that the descriptions are contextually relevant.

### Wave 11.5-B (serial follow-up after Wave 11.5-A)

Task 11.5-B-1
Developer @dev-frank
Files allowed:
└─ tests/integration/test_pickup_scenario_obstacle_resolution.py
└─ agent_world/scenarios/default_pickup_scenario.py (if minor adjustments needed for testability)
Outline:
• Create a new integration test (`test_pickup_scenario_obstacle_resolution.py`) that runs the `DefaultPickupScenario`.
• This test must verify that the agent, when faced with the obstacle:
    1.  Identifies the obstacle (either through planning or reactive prompting).
    2.  Decides to generate an ability to remove/bypass the obstacle.
    3.  Successfully requests and is granted a generic "remove obstacle" type ability by the Angel System (mock LLM for Angel to return a simple, functional "print and remove obstacle" stub if true code generation is too flaky for this test).
    4.  Uses the newly acquired ability to clear the obstacle.
    5.  Proceeds to pick up the target item.
• This test will serve as a key validation for the success of Phase 11.5.

This phase is designed to be a focused effort. If these tasks are completed successfully, the agents should be noticeably more capable of basic problem-solving involving obstacles, setting a much stronger foundation for the complex interactions planned in Phase 12.


## Phase 12 · Deepening Gameplay Systems & Agent Interaction

Integrate AI decision-making more deeply into existing gameplay systems, allowing agents to intelligently interact with the world and each other.

### Wave 12-A (parallel)

Task 12-A-1
Developer @dev-alice
Files allowed:
└─ agent_world/systems/interaction/trading.py
└─ agent_world/ai/llm/prompt_builder.py (for exposing trade info)
└─ agent_world/core/components/ai_state.py (if goals need trade-specific extensions)
└─ tests/systems/interaction/test_ai_trading.py
Outline:
• Enhance `TradingSystem` to support offers, counter-offers, or at least valuation-based decisions using `get_local_prices`.
• Agents (via `AIReasoningSystem` + `LLMPlanner` or specialized BTs) should be able to form goals like "acquire X by trading Y."
• Expose local prices and potential trade partners/inventory to agent prompts.
• Test a scenario where an agent decides to trade based on its goals and perceived market conditions.

Task 12-A-2
Developer @dev-bob
Files allowed:
└─ agent_world/systems/interaction/crafting.py
└─ agent_world/ai/llm/prompt_builder.py (for exposing recipe/inventory info)
└─ agent_world/core/components/ai_state.py (if goals need craft-specific extensions)
└─ agent_world/data/recipes.json (expand with more complex recipes)
└─ tests/systems/interaction/test_ai_crafting.py
Outline:
• Expand `recipes.json` with a few more complex recipes.
• Agents need to be able to "learn" or be granted knowledge of recipes (e.g., add `known_recipes: list[str]` to `AIState` or a new component).
• Agents (via `AIReasoningSystem` + `LLMPlanner` or specialized BTs) should decide to craft items based on goals, known recipes, and available inventory.
• Expose known recipes and inventory to agent prompts.
• Test a scenario where an agent gathers resources and crafts an item to fulfill a goal.

Task 12-A-3
Developer @dev-carol
Files allowed:
└─ agent_world/systems/combat/combat_system.py
└─ agent_world/systems/combat/damage_types.py
└─ agent_world/systems/combat/defense.py
└─ agent_world/ai/llm/prompt_builder.py (for exposing combat info)
└─ agent_world/ai/behaviors/combat_bt.py (new)
└─ tests/systems/combat/test_ai_combat.py
Outline:
• Add 1-2 new `DamageType`s (e.g., `FIRE`, `MAGIC`) and update `Defense` component to handle them.
• Create `agent_world/ai/behaviors/combat_bt.py` with a more sophisticated behavior tree for combat (e.g., choose target, use appropriate ability, consider retreating if low health).
• Agents (LLM-driven or BT-driven) should make tactical combat decisions, potentially choosing abilities from `KnownAbilitiesComponent`.
• Expose relevant combat information (target health, own health, nearby threats) to prompts.
• Test scenarios with different combat situations and agent responses.

Task 12-A-4
Developer @dev-dave
Files allowed:
└─ agent_world/data/roles.yaml
└─ agent_world/utils/cli/commands.py (spawn command if needs updates for new role features)
└─ agent_world/systems/ai/ai_reasoning_system.py (if role-specific plan generation is needed)
└─ tests/ai/test_richer_npc_roles.py
Outline:
• Define 2-3 new NPC roles in `roles.yaml` with distinct `fixed_abilities`, `can_request_abilities`, and `uses_llm` settings.
• These roles should leverage the improved AI/planning and gameplay systems (e.g., a "Trader" role that prioritizes trading goals, a "Crafter" role).
• Ensure the AI systems (`AIReasoningSystem`, `BehaviorTreeSystem`) can differentiate behaviors or default plans based on these richer roles.
• Test that NPCs with new roles exhibit distinct behaviors.

## Phase 13 · Full Procedural Generation & World Richness

Fully realize the "procedural everything" philosophy, particularly for items and potentially more complex map features.

### Wave 13-A (parallel)

Task 13-A-1
Developer @dev-ellen
Files allowed:
└─ agent_world/core/components/item.py (new)
└─ agent_world/systems/interaction/pickup.py
└─ agent_world/systems/interaction/crafting.py
└─ agent_world/utils/asset_generation/item_generator.py (new)
└─ agent_world/utils/cli/commands.py (for spawning proc-gen items)
└─ tests/procedural_generation/test_item_generation.py
Outline:
• Create `ItemComponent` dataclass to hold properties (e.g., name, description, effects, value, type) for items.
• Create `item_generator.py` to procedurally generate `ItemComponent` instances with varied properties.
• Modify `PickupSystem` and `CraftingSystem` to work with `ItemComponent` instead of just entity IDs for items.
• Update `spawn` CLI command: `/spawn item [type]` could now use the item generator.
• Test procedural item generation and its integration with inventory/crafting.

Task 13-A-2
Developer @dev-frank
Files allowed:
└─ agent_world/core/world.py (resource/map generation)
└─ agent_world/utils/asset_generation/map_features.py (new)
└─ tests/procedural_generation/test_map_features.py
Outline:
• Create `map_features.py` to define procedures for generating more complex map features (e.g., small structures, varied resource clusters, named locations).
• Enhance `World.generate_resources` or add a new `World.generate_map_features` method to incorporate these.
• These features should be deterministic and potentially influence agent behavior (e.g., a "ruin" might contain rare items).
• Test generation of new map features.

## Phase 14 · Advanced Observability, Replay, & CLI

Enhance tools for observing, debugging, and interacting with the simulation to support the analysis of emergent behavior.

### Wave 14-A (parallel)

Task 14-A-1
Developer @dev-grace
Files allowed:
└─ agent_world/persistence/replay.py
└─ agent_world/persistence/event_log.py (if new event types needed for replay)
└─ tests/persistence/test_advanced_replay.py
Outline:
• Enhance `replay.py` to robustly handle all logged event types from the persistent event log, including LLM I/O and Angel actions.
• Develop more comprehensive replay tests that verify complex sequences of events leading to specific world states or agent decisions.
• Ensure that replaying a logged scenario results in a deterministic outcome matching the original run as closely as possible (given LLM stochasticity, focus on replaying decisions and actions).

Task 14-A-2
Developer @dev-heidi
Files allowed:
└─ agent_world/utils/cli/commands.py
└─ agent_world/ai/angel/system.py (for manual trigger integration)
└─ tests/cli/test_advanced_cli_commands.py
Outline:
• Add new CLI commands:
    • `/angel trigger <agent_id> "<description>"` to manually trigger an Angel System request for a specific agent and description.
    • `/agent inspect <agent_id> <memory|goals|plan>` to view detailed internal states of an agent.
    • `/world set_state <key> <value>` (e.g., `/world set_state time_scale 2.0`) for basic world state manipulation (add `time_scale` to `TimeManager` if implementing).
• Test these new CLI commands thoroughly.

Task 14-A-3
Developer @dev-ivan
Files allowed:
└─ agent_world/gui/renderer.py
└─ agent_world/gui/input.py
└─ tests/gui/test_debug_overlays.py
Outline:
• Enhance the GUI `Renderer` to display more debug information as overlays.
• Examples: agent goals, current action/plan, visual representation of perception radius, paths being considered.
• Add keybindings in `gui/input.py` to toggle these debug overlays.
• Test that overlays can be toggled and display correct information.

## Phase 15 · Polish, Balancing, & Final PDD Alignment

Refine all systems, balance gameplay interactions, ensure all aspects align with the final PDD vision, and perform extensive testing for stability and emergent behavior.

### Wave 15-A (Iterative & Parallel)

Task 15-A-1 (Ongoing)
Developer @dev-alice
Files allowed:
└─ Various config files (roles.yaml, recipes.json)
└─ Various system files (combat, trading, crafting, ability costs)
└─ tests/integration/test_balance_and_emergence.py
Outline:
• Iteratively balance ability costs, cooldowns, item values, crafting recipe difficulty, combat parameters.
• Create complex, long-running integration tests designed to observe and validate emergent behaviors (e.g., can an agent identify a need, request/craft a tool/ability, and then use it to achieve a multi-step goal?).
• Log metrics related to game economy, agent survival, goal completion rates.

Task 15-A-2
Developer @dev-bob
Files allowed:
└─ Entire codebase
└─ tests/ (adding performance tests)
Outline:
• Conduct performance profiling across the application.
• Identify and optimize bottlenecks in critical systems (e.g., spatial index, rendering, frequent component access).
• Ensure the simulation runs smoothly with a target number of entities and maintains the soft tick budget.

Task 15-A-3 (Final Review)
Developer @dev-carol
Files allowed:
└─ PROJECT_DESIGN.md
└─ README.md
└─ Entire codebase (for documentation and final checks)
Outline:
• Perform a final review of the `PROJECT_DESIGN.md` to ensure it accurately reflects the completed project state.
• Update `README.md` with final usage instructions, features, and project summary.
• Add/update comments and docstrings throughout the codebase.
• Address any remaining minor bugs, inconsistencies, or TODOs identified during balancing and testing.
• Ensure test coverage remains high (≥95%).
