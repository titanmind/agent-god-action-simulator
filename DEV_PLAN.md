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
    agent_decision_model: "default/model"     # Placeholder, actual model ID can vary
    angel_generation_model: "default/model"   # Placeholder

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