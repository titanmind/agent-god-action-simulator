## Agent World Simulator — Project Design Document (vFuture)

*This document outlines the envisioned state of the Agent World Simulator, incorporating advanced AI-driven agent capabilities and dynamic world interactions.*

---

### 0 · Snapshot

A **Python-only, single-process sandbox** that marries a lightweight Entity-Component-System (ECS) architecture with sophisticated, LLM-driven autonomous agents. Features include dynamic ability generation via an "Angel" LLM, diverse NPC roles, observational learning, deterministic replay, and wholly-procedural art. The simulation is designed to be run with a simple `python main.py`, requiring no external services beyond an optional LLM API key.

---

## 1 · Core Philosophy

*   **Self-hosted hobby project** – prioritize simplicity and direct control over enterprise-grade operational complexity.
*   **Monolith over micro-services** – maintain a single interpreter environment, utilizing threads and asyncio for concurrency.
*   **Procedural everything** – all assets (sprites, maps, items, abilities) are generated at runtime or based on defined procedures, minimizing external dependencies.
*   **Deterministic by default** – core simulation logic is deterministic. LLM interactions are managed for replayability, with offline modes for testing and CI.
*   **Test-driven, modular** – high test coverage, with a codebase structured for clarity and maintainability.
*   **Emergent Behavior Focus** – the primary goal is to create a sandbox where complex and interesting agent behaviors can emerge from well-defined rules and LLM-driven decision-making.

---

## 2 · Runtime Architecture

```
main.py
├── Main Tick Loop (sync)
│   ├─ IF NOT world.paused_for_angel:
│   │  ├─ SystemsManager.update()          // Processes all game systems
│   │  │  ├─ PhysicsSystem
│   │  │  ├─ ActionExecutionSystem      // Consumes agent actions
│   │  │  ├─ AIReasoningSystem          // Handles agent LLM decisions & BT fallbacks
│   │  │  ├─ AbilitySystem              // Manages ability loading & cooldowns
│   │  │  ├─ AngelSystem                // Registered but idle unless paused
│   │  │  └─ … other gameplay systems …
│   │  └─ TimeManager.sleep_until_next_tick() // Advances game time
│   └─ AngelSystem.process_pending_requests() // Runs if world.paused_for_angel IS True
│      └─ (Manages LLM calls for ability generation, Vault search, sandboxed testing)
├── GUI Thread / Tick Hook (pygame)
│   └─ Renderer.update(world)             // Visualizes world state
├── LLM Worker Pool (asyncio)              // For agent action decisions & Angel LLM calls
├── Persistence Task                       // Incremental and full world state saves
└── CLI Input Thread                       // For developer interaction
```
*   **World Pause for Angel:** When an agent requests an ability, the main tick loop pauses other systems. `AngelSystem.process_pending_requests()` runs until generation completes.
*   *Soft budget* 100 ms per game tick (when not paused for Angel); overruns logged.

---

## 3 · LLM Integration & The Angel System

*   **Agent Decision LLM:**
    *   Used by `AIReasoningSystem` for agents capable of complex thought to decide actions based on their state, goals, and perception.
    *   Modes: `offline` (scripted/wait), `echo`, `live` (OpenRouter).
    *   Prompt Pipeline: `PerceptionSystem output → world_view → prompt_builder → LLMManager.request() → action parsing → ActionQueue`.
*   **Angel System (Advanced Ability Generation & Granting):**
    *   **Invocation:** Triggered by an agent's `GENERATE_ABILITY` action. Pauses the main world simulation.
    *   **Responsibilities:**
        1.  **Vault Search:** First, attempts to semantically match the agent's request against a curated "Vault" of pre-built, robust abilities (`abilities/vault/`). If a match is found, it grants this existing ability.
        2.  **LLM-Powered Code Generation:** If no Vault match, the Angel System uses its own (potentially more powerful) LLM instance to write new Python ability code. This LLM is prompted with the request, relevant world constraints, and ability code templates/scaffolds.
        3.  **Conceptual Testing:** The Angel's LLM only reasons about potential tests; generated code is not executed under `RestrictedPython` at runtime.
        4.  **Ability Granting:** Upon successful generation or Vault selection, the ability's class name is added to the requesting agent's `KnownAbilitiesComponent`.
        5.  **Agent Turn Redo:** After the Angel completes and unpauses the world, the requesting agent immediately gets to re-evaluate its turn, now aware of the new ability, bypassing its normal LLM cooldown for this single re-evaluation.
    *   **Output:** Generated Python ability files are saved to `agent_world/abilities/generated/`.

---

## 4 · ECS Core & Agent Specialization

### 4.1 Key Components

```
PositionComponent        (x, y)
PhysicsComponent         (vx, vy, mass, friction)
ForceComponent           (dx, dy, ttl)
HealthComponent          (cur, max)
InventoryComponent       (capacity, items)
AIStateComponent         (personality, goals_list, pending_prompt_id, last_action_tick, last_bt_move_failed)
PerceptionCacheComponent (visible_entities, visible_ability_uses, last_tick)
KnownAbilitiesComponent  (known_ability_class_names_list) // NEW
RoleComponent            (role_name, can_request_abilities, uses_llm, fixed_abilities_list) // NEW
OwnershipComponent       (owner_id)
RelationshipComponent    (faction, reputation_map)
```

### 4.2 Managers & Index

*   `EntityManager`: Manages entity lifecycles.
*   `ComponentManager`: Manages component registration and entity-component association.
*   `SpatialGrid`: Efficient spatial querying.

---

## 5 · Gameplay Systems (Illustrative Order)

```
systems/
├ movement/            MovementSystem, PhysicsSystem, pathfinding_utils
├ perception/          PerceptionSystem (tracks visible entities & ability uses)
├ interaction/         PickupSystem, TradingSystem, CraftingSystem
├ ability/             AbilitySystem (loads all abilities, manages cooldowns globally)
├ ai/                  AIReasoningSystem (differentiates by RoleComponent, manages agent LLM calls & BTs)
│                      ActionExecutionSystem (processes ActionQueue, invokes AngelSystem, checks KnownAbilitiesComponent)
│                      AngelSystem (handles ability requests, Vault, LLM generation, granting)
├ combat/              CombatSystem
└ … other systems …
```
*   `ActionExecutionSystem` will verify an agent possesses an ability (via `KnownAbilitiesComponent`) before allowing `AbilitySystem.use()`.
*   `PerceptionSystem` populates each agent's `PerceptionCacheComponent.visible_ability_uses` list for prompt building.

---

## 6 · GUI & Input

*   **No Player Character:** The simulation focuses entirely on AI agents.
*   **Enhanced Camera:** GUI offers robust camera controls (pan, zoom, follow selected agent).
*   **Renderer:** Visualizes all entities, tilemap, and debug overlays.
*   **CLI Primary Interaction:** Developer interaction for spawning, inspection, and direct commands via the CLI.

---

## 7 · Abilities: Vault, Generated, and Known

*   **Base Class:** `abilities.base.Ability` (`can_use`, `execute`, `cost`, `cooldown`).
*   **Ability Sources:**
    *   `abilities/builtin/`: Core, developer-defined abilities always available.
    *   `abilities/vault/`: Curated, complex, developer-defined abilities discoverable by the Angel System.
    *   `abilities/generated/`: Abilities dynamically created by the Angel System's LLM.
*   **Loading:** `AbilitySystem` loads all valid ability modules from these locations on startup and via hot-reloading for `generated/`.
*   **Agent Access:** An agent can only *attempt to use* abilities whose class names are present in its `KnownAbilitiesComponent`.
*   **Dynamic Code Generation:** The Angel System's LLM generates Python code for new abilities, which is then written to disk and loaded. No runtime `RestrictedPython` sandbox for *execution* of abilities once loaded (they become normal Python code), but the Angel's LLM is guided towards safe generation practices.

---

## 8 · Persistence & Replay

*   **Full Snapshot & Incremental Deltas:** Unchanged.
*   **Event Log:** All major systems append structured events to a persistent log file (`world.persistent_event_log_path`) via `event_log.append_event`. This captures LLM prompts/responses, Angel actions, combat and crafting results, and other world events for replay.

---

## 9 · Observability & CLI

*   **Enhanced CLI:** Robust commands for spawning agents with specific roles, inspecting `KnownAbilitiesComponent` and `RoleComponent`, triggering Angel requests manually for testing, and manipulating world state.
*   **Detailed Logging:** Comprehensive logging of LLM interactions (full prompts and raw responses), Angel System decisions, and agent reasoning steps.
*   **Standard Logging:** Debug output now uses Python's `logging` module instead of `print` calls.

---

## 10 · Procedural Asset Generation & Caches

*   Unchanged (sprites, map resources).

---

## 11 · Testing & Determinism

*   Focus on testing individual system logic, agent decision paths with mocked LLM/Angel responses, and the deterministic replay of event logs.
*   End-to-end tests will verify scenarios like: agent identifies problem → requests ability → Angel grants/creates ability → agent uses new ability successfully.

---

## 12 · Configuration Skeleton (`config.yaml`)

The file is loaded through `agent_world.config.CONFIG`, providing dataclass access across the codebase.

```yaml
world:
  size:            [100, 100]
  tick_rate:       10
  max_entities:    8000
  paused_for_angel_timeout_seconds: 60

llm:
  mode: offline
  agent_decision_model:  <model_identifier_for_agents>
  angel_generation_model: <model_identifier_for_angel_code_gen>

paths:
  abilities_vault: "./agent_world/abilities/vault"
  abilities_generated: "./agent_world/abilities/generated"
  abilities_builtin: "./agent_world/abilities/builtin"

cache:
  sprite_max: 10000
  log_retention_mb: 50
```

---

### 13 · Vision Summary

The simulator evolves into a dynamic ecosystem where AI agents not only act based on LLM-driven reasoning but can also actively expand their capabilities through interaction with a sophisticated "Angel" system. This Angel can intelligently grant pre-existing complex abilities from a Vault or orchestrate the LLM-powered generation of entirely new, situationally relevant abilities. Different NPC roles with fixed or LLM-driven behaviors and distinct skill sets create a richer world. The removal of a dedicated player entity sharpens the focus on emergent AI-vs-AI and AI-vs-environment interactions, observed and guided through enhanced CLI and logging. The core remains a testable, deterministic-as-possible Python sandbox for exploring advanced AI agent concepts.