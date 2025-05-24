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

### Wave 5-B  (serial)

Task 5-B-1
Developer @dev-zoe
Files allowed:
└─ agent\_world/systems/ai/actions.py
└─ agent\_world/utils/cli/commands.py
└─ tests/core/test\_no\_player\_constant.py
Outline:
• remove `PLAYER_ID` constant; refactor remaining helper code to avoid special case
• update affected tests

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
