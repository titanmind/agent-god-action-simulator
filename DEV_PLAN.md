Below is a **phased, wave-based build roadmap** designed for a single-repo, Python-only project.
*Every task is self-contained, names the exact files that may be touched, and assigns one developer handle.*
Follow the waves in order; do **not** start a later wave until all tasks in the current wave have merged cleanly.
Remember: **no external art or assets** – everything visual will later be generated procedurally.
**Mark Tasks, Waves, and Phases Complete** when you complete them by adding a checkmark next to them.

---

## Phase 1 · Core Foundation

### Wave 1-A (3 parallel tasks)

```
Task 1-A-1
Developer @dev-alice
Files allowed to edit:
  └─ agent_world/core/world.py
Task outline:
  • Implement World(size) with tile map and stubs for add/remove entity and system registration.
  • Hold references to managers (populated later).
Reinforcement:
  - Std-lib only.

✓ Task 1-A-2
Developer @dev-bob
Files allowed to edit:
  └─ agent_world/core/entity_manager.py
Task outline:
  • Global unique-ID generator, create_entity(), destroy_entity().
  • Store entity → component-dict map.
Reinforcement:
  - No game logic.

Task 1-A-3 ✓
Developer @dev-charlie
Files allowed to edit:
  └─ agent_world/core/component_manager.py
Task outline:
  • Registry of component classes and helpers add/get/remove component.
  • Leave registration hooks empty for now.
Reinforcement:
  - Must compile without other core modules present.
```

### Wave 1-B (2 parallel tasks, after 1-A)

```
✓ Task 1-B-1
Developer @dev-dana
Files allowed to edit:
  └─ agent_world/core/components/position.py
  └─ agent_world/core/components/health.py
  └─ agent_world/core/components/inventory.py
Task outline:
  • Define dataclasses Position(x,y), Health(cur,max), Inventory(capacity, items=list).
Reinforcement:
  - Pure data only.

Task 1-B-2
Developer @dev-elliot
Files allowed to edit:
  └─ agent_world/core/components/ai_state.py
  └─ agent_world/core/components/perception_cache.py
Task outline:
  • AIState(personality, goals=list) and PerceptionCache(visible=list, last_tick).
Reinforcement:
  - No external deps.
```

### Wave 1-C (2 parallel tasks, after 1-B)

```
Task 1-C-1
Developer @dev-fay
Files allowed to edit:
  └─ agent_world/core/time_manager.py
Task outline:
  • Tick loop helpers: tick_rate, tick_counter, sleep_until_next_tick().
  • Blocking sleep only; unit test in file.

✓ Task 1-C-2
Developer @dev-glen
Files allowed to edit:
  └─ agent_world/core/spatial/spatial_index.py
  └─ agent_world/core/spatial/quadtree.py
Task outline:
  • SpatialGrid(cell_size) with insert/remove/query_radius.
  • Thin Quadtree wrapper for future optimisation.
```

---

## Phase 2 · Base Gameplay Systems

### Wave 2-A (4 parallel tasks)

```
Task 2-A-1
Developer @dev-hana
Files allowed to edit:
  └─ agent_world/systems/movement/movement_system.py
Task outline:
  • Move entities with Position & Velocity (define Velocity dataclass here).
  • Update spatial index.

✓ Task 2-A-2
Developer @dev-ian
Files allowed to edit:
  └─ agent_world/systems/movement/pathfinding.py
Task outline:
  • A* grid path-finder returning list[(x,y)].
  • Stub heuristics; no obstacles yet.

Task 2-A-3
Developer @dev-jade
Files allowed to edit:
  └─ agent_world/systems/perception/perception_system.py
  └─ agent_world/systems/perception/line_of_sight.py
Task outline:
  • Populate PerceptionCache using SpatialGrid.
  • Simple LOS: distance check only.

Task 2-A-4
Developer @dev-root
Files allowed to edit:
  └─ agent_world/main.py   (# only BOOTSTRAP section)
Task outline:
  • Glue World, managers and systems; run 10 dummy ticks printing tick id.
```

### Wave 2-B (3 parallel tasks, after 2-A)

```
✓ Task 2-B-1
Developer @dev-alice
Files allowed to edit:
  └─ agent_world/systems/combat/combat_system.py
  └─ agent_world/systems/combat/damage_types.py
Task outline:
  • Melee range check 1; subtract 10 HP; log event.

Task 2-B-2
Developer @dev-bob
Files allowed to edit:
  └─ agent_world/systems/interaction/pickup.py
Task outline:
  • If Position equal and other has tag "item", move to Inventory.

Task 2-B-3
Developer @dev-charlie
Files allowed to edit:
  └─ agent_world/core/systems_manager.py
Task outline:
  • Registry to add/remove systems and iterate them each tick in order.
```

---

## Phase 3 · LLM Integration

### Wave 3-A (3 parallel tasks)

```
Task 3-A-1
Developer @dev-dana
Files allowed to edit:
  └─ agent_world/ai/llm/llm_manager.py
  └─ agent_world/ai/llm/cache.py
Task outline:
  • Async queue, in-memory LRU cache, stubbed request() returns "<wait>".

Task 3-A-2
Developer @dev-elliot
Files allowed to edit:
  └─ agent_world/ai/llm/prompt_builder.py
Task outline:
  • build_prompt(agent_id, world_view) deterministic template.

Task 3-A-3
Developer @dev-fay
Files allowed to edit:
  └─ agent_world/systems/ai/ai_reasoning_system.py
Task outline:
  • For each agent with AIState, enqueue prompt; timeout 0.05 s; enqueue action string.
```

### Wave 3-B (1 task, after 3-A)

```
Task 3-B-1
Developer @dev-glen
Files allowed to edit:
  └─ agent_world/systems/ai/actions.py
  └─ agent_world/main.py   (# AI HOOK only)
Task outline:
  • Parse action strings "MOVE N" "ATTACK id" into world-safe action objects and queue for execution in subsequent ticks.
```

### Wave 3-C (1 task, after 3-B)

```
Task 3-C-1
Developer @dev-zoe
Files allowed to edit:
  └─ agent_world/ai/llm/llm_manager.py
  └─ agent_world/main.py (BOOTSTRAP section only)
  └─ pyproject.toml ([project] dependencies)
  └─ README.md (brief usage note)
Task outline:
  • Add python-dotenv to pyproject.toml and document the install line.
  • Load env-vars once at bootstrap:
    • in main.bootstrap(), call dotenv.load_dotenv() if a .env file exists.
    • respect two variables: OPENROUTER_API_KEY, OPENROUTER_MODEL.
  • Wire into LLMManager:
    • accept api_key and model kwargs; default to the env-vars.
    • if either is missing or the runtime has no internet (detectable via a simple socket.gethostbyname("openrouter.ai") wrapped in try/except) → keep returning "<wait>" exactly as today (no functional change for Codex agents).
  • Update README with a “Getting Started – LLM access” blurb that shows a sample .env:
    ```bash
    OPENROUTER_API_KEY=sk-…
    OPENROUTER_MODEL=openai/gpt-4o
    ```
Reinforcement:
  - No other files may be touched. Unit tests must still pass with and without a .env present. Codex CI lacks web; therefore tests must mock any network call.
Acceptance Criteria:
  * Running python main.py on a dev machine that has a filled-in .env should print “LLM online: <model>”.
  * In CI / sandbox (no .env or outbound net) behaviour is unchanged and unit tests remain green.
Notes for reviewers:
  Codex build agents still cannot reach OpenRouter, so this task should not attempt a real HTTP request in tests—mock or short-circuit instead.
```

---

## Phase 4 · Persistence & Replay

### Wave 4-A (3 parallel tasks)

```
Task 4-A-1
Developer @dev-hana
Files allowed to edit:
  └─ agent_world/persistence/save_load.py
  └─ agent_world/persistence/serializer.py
Task outline:
  • snapshot/world JSON, gzip option.

Task 4-A-2
Developer @dev-ian
Files allowed to edit:
  └─ agent_world/persistence/event_log.py
Task outline:
  • JSONL append {tick, event_type, data}.  Replay iterator.

Task 4-A-3
Developer @dev-jade
Files allowed to edit:
  └─ agent_world/persistence/replay.py
Task outline:
  • Re-run world ticks feeding stored events; verify determinism.
```

### Wave 4-B (1 task, after 4-A)

```
✓ Task 4-B-1
Developer @dev-root
Files allowed to edit:
  └─ agent_world/main.py   (# PERSISTENCE HOOK only)
Task outline:
  • Auto-save every 60 s, load on start.
```

---

## Phase 5 · Dynamic Abilities & Sandbox

### Wave 5-A (3 parallel tasks)

```
Task 5-A-1
Developer @dev-alice
Files allowed to edit:
  └─ agent_world/abilities/base.py
Task outline:
  • Define Ability interface: can_use, execute, energy_cost, cooldown.

Task 5-A-2
Developer @dev-bob
Files allowed to edit:
  └─ agent_world/utils/sandbox.py
Task outline:
  • run_in_sandbox(code_str) with RestrictedPython, 50 ms timeout, no imports beyond math.

✓ Task 5-A-3
Developer @dev-charlie
Files allowed to edit:
  └─ agent_world/ai/angel/generator.py
Task outline:
  • generate_ability(desc) → write scaffold file to abilities/generated/.
```

### Wave 5-B (1 task, after 5-A)

```
Task 5-B-1
Developer @dev-dana
Files allowed to edit:
  └─ agent_world/systems/ability/ability_system.py
  └─ agent_world/systems/ability/cooldowns.py
Task outline:
  • Load, hot-reload, and execute abilities; track per-entity cooldowns.
```

---

## Phase 6 · CLI, Profiling & Observer

### Wave 6-A (3 parallel tasks)

```
Task 6-A-1
Developer @dev-elliot
Files allowed to edit:
  └─ agent_world/utils/observer.py
Task outline:
  • dump_state(), rolling tick deque, print_fps().

Task 6-A-2
Developer @dev-fay
Files allowed to edit:
  └─ agent_world/utils/profiling.py
Task outline:
  • cProfile wrapper profile_ticks(n).

Task 6-A-3
Developer @dev-glen
Files allowed to edit:
  └─ agent_world/utils/cli/commands.py
  └─ agent_world/utils/cli/command_parser.py
  └─ agent_world/main.py  (# CLI HOOK only)
Task outline:
  • Implement /pause, /step, /save, /reload abilities, /profile.
```

---

## Phase 7 · Procedural Asset Generation

### Wave 7-A (1 task)

```
Task 7-A-1
Developer @dev-hana
Files allowed to edit:
  └─ agent_world/utils/asset_generation/sprite_gen.py
  └─ agent_world/utils/asset_generation/noise.py
  └─ assets/ (runtime only)
Task outline:
  • Generate 32×32 PNG sprites (solid colour + ID text) via Pillow.
  • get_sprite(entity_id) cache & return PIL.Image.
```

---

## Phase 8 — Core Gameplay Polish

```
Wave 8-A  (run in parallel)

Task 8-A-1
Developer @dev-alice
Files allowed:
  └─ agent_world/systems/combat/defense.py
  └─ agent_world/systems/combat/combat_system.py
Outline:
  • Add armor & dodge using DamageType look-ups.
  • Emit “death” event when Health.cur ≤ 0.

Task 8-A-2
Developer @dev-bob
Files allowed:
  └─ agent_world/systems/interaction/trading.py
  └─ agent_world/systems/interaction/stealing.py
Outline:
  • Implement simple barter + reputation penalty on theft.

Task 8-A-3
Developer @dev-charlie
Files allowed:
  └─ agent_world/systems/movement/movement_system.py
  └─ agent_world/systems/movement/pathfinding.py
Outline:
  • Add obstacle grid & collision resolve; update A* to respect obstacles.
```

```
Wave 8-B  (after 8-A)

Task 8-B-1
Developer @dev-dana
Files allowed:
  └─ agent_world/utils/observer.py
  └─ agent_world/utils/profiling.py
Outline:
  • Integrate `print_fps()` into main loop; add `observer.record_tick()`.
  • Provide CLI `/fps` to toggle live read-out.
```

---

## Phase 9 — Advanced Agent Cognition

```
Wave 9-A

Task 9-A-1
Developer @dev-elliot
Files allowed:
  └─ agent_world/ai/memory.py  (new)
Outline:
  • Vector-store-like short-term memory ring; prune on overflow.
  • Expose `retrieve(agent_id, k)` for prompt_builder.

Task 9-A-2
Developer @dev-fay
Files allowed:
  └─ agent_world/ai/llm/prompt_builder.py
Outline:
  • Inject top-K memory snippets into prompt template.
```

```
Wave 9-B  (after 9-A)

✓ Task 9-B-1
Developer @dev-glen
Files:
  └─ agent_world/systems/ai/behavior_tree.py
Outline:
  • Draft three-node BT (Selector → Sequence → Action) and plug into AIReasoningSystem for fallback when LLM returns `<wait>`.
```

Sources on AI memory & planning ([Medium][12]).

---

## Phase 10 — Visualization & Debug UI

Minimal ANSI or Ascii-map view lets designers *see* combat & path-finding:

```
Wave 10-A

Task 10-A-1
Developer @dev-hana
Files:
  └─ agent_world/utils/cli/terminal_view.py  (new)
Outline:
  • Render 40×20 chunk of tile_map with glyph per sprite colour.
  • Hook `/view [radius]` to toggle live redraw every tick.
```

---

## Phase 11 — Performance & Scalability Pass ✓

* **Profiling async sections** with techniques from recent guides ([Medium][13]). ✓
* Stress-test 5 k entities; optimize SpatialGrid (batch inserts) and A\* (early exit). ✓

---

## Phase 12 — Content & Economy

* Crafting graph, resource nodes, faction economy loops; governed by configurable YAML tuned via replay analytics.

---

## Phase 13 · Stub Smash & Core Completeness
_Eliminate every “# Placeholder” and finish the core data model._

### Wave 13-A (3 parallel tasks)

```

Task 13-A-1
Developer **@dev-alice**
Files allowed:
└─ agent\_world/core/components/physics.py
└─ agent\_world/systems/movement/movement\_system.py
Outline:
• Implement `Physics(mass:float, vx:float, vy:float, friction:float)` dataclass.
• Extend `MovementSystem` to integrate velocity from `Physics` if a `Velocity` component is absent.
• Cap speed by friction each tick.

Task 13-A-2
Developer **@dev-bob**
Files allowed:
└─ agent\_world/core/components/ownership.py
└─ agent\_world/systems/interaction/pickup.py
Outline:
• Define `Ownership(owner_id:int)`; update `PickupSystem` to copy ownership when items are picked up.

Task 13-A-3
Developer **@dev-charlie**
Files allowed:
└─ agent\_world/core/components/relationship.py
└─ agent\_world/systems/interactions/stealing.py
└─ agent\_world/systems/interactions/trading.py
Outline:
• Implement `Relationship(faction:str, reputation:int)`.
• Factor reputation deltas (+/-) into Stealing & Trading systems.

```

### Wave 13-B (2 parallel tasks)

```

Task 13-B-1
Developer **@dev-dana**
Files allowed:
└─ agent\_world/utils/hot\_reload.py
Outline:
• File-watcher (polling) that notices changes in any `abilities/generated/*.py` file and triggers a callback (`on_change`).
• Must run in a lightweight thread; no external deps.

Task 13-B-2
Developer **@dev-elliot**
Files allowed:
└─ agent\_world/utils/asset\_generation/color\_palettes.py
Outline:
• Provide a deterministic HSV → RGB palette generator.
• Expose `get_palette(faction:str, n:int)` returning list\[tuple\[int,int,int]].
• Used by `sprite_gen.py` if available.

```

### Wave 13-C (1 task)

```

Task 13-C-1
Developer **@dev-fay**
Files allowed:
└─ agent\_world/persistence/incremental\_save.py
└─ agent\_world/main.py   (# PERSISTENCE HOOK only)
Outline:
• Implement delta-compression snapshots every **5 ticks**; store under `saves/<world_id>/increments/`.
• Hook into the existing auto-save thread.
• Provide `load_incremental(path)` helper for replays.

```

### Wave 13-D (2 parallel tasks)

```

Task 13-D-1
Developer **@dev-glen**
Files allowed:
└─ agent\_world/abilities/builtin/melee.py
Outline:
• Built-in `MeleeStrike` ability that calls `CombatSystem.attack()` and respects energy/cooldown.

Task 13-D-2
Developer **@dev-hana**
Files allowed:
└─ agent\_world/abilities/builtin/ranged.py
Outline:
• `ArrowShot` ability with LOS check & ammo cost (consume item from `Inventory`).

```

---

## Phase 14 · Crafting + Resource Loop

### Wave 14-A (2 parallel tasks)

```

Task 14-A-1
Developer **@dev-ian**
Files allowed:
└─ agent\_world/systems/interaction/crafting.py
Outline:
• JSON-driven recipe table (`recipes.json` under project root).
• `craft(entity_id, recipe_id)` consumes inputs from `Inventory`, produces outputs, and logs an event.

Task 14-A-2
Developer **@dev-jade**
Files allowed:
└─ agent\_world/utils/asset\_generation/noise.py
└─ agent\_world/core/world.py
Outline:
• Procedurally place “resource nodes” (ore, wood, herbs) on the map using white‐noise thresholding.
• Expose `World.spawn_resource(kind, x, y)` helper.

```

### Wave 14-B (after 14-A)

```

Task 14-B-1
Developer **@dev-root**
Files allowed:
└─ agent\_world/systems/interaction/trading.py
└─ agent\_world/ai/llm/prompt\_builder.py
Outline:
• Dynamic price model: every resource + item gets a `base_value`; adjust by local supply (count in 10-tile radius).
• Expose prices to LLM via prompt\_builder so agents can reason about profit.

```

---

## Phase 15 · CLI & Debug Finishing Touches

### Wave 15-A (2 parallel tasks)

```

Task 15-A-1
Developer **@dev-zoe**
Files allowed:
└─ agent\_world/utils/cli/commands.py
└─ agent\_world/utils/observer.py
Outline:
• Add `/fps` command → toggle `observer.toggle_live_fps()`.
• Print FPS each tick when enabled.

Task 15-A-2
Developer **@dev-alice**
Files allowed:
└─ agent\_world/utils/cli/commands.py
└─ agent\_world/utils/cli/command\_parser.py
Outline:
• Implement `/spawn <ability|item|npc>` and `/debug <entity_id>` (prints component dump).
• Both commands must be non-blocking and safe when the world is paused.

```

---

## Phase 16 · Physics System

### Wave 16-A (1 task)

```

Task 16-A-1
Developer **@dev-bob**
Files allowed:
└─ agent\_world/systems/movement/physics\_system.py   (new)
└─ agent\_world/core/systems\_manager.py
Outline:
• New `PhysicsSystem` integrates forces → velocity, applies basic collision resolution vs OBSTACLES.
• Register into SystemsManager before MovementSystem.

```

---

## Phase 17 · Core Loop Integration & Physics Feedback
*Objective: wire the real tick-loop end-to-end, add force/impulse handling, and
surface collision data for AI & logs.*

### Wave 17-A (3 parallel tasks)

```

Task 17-A-1
Developer **@dev-root**
Files allowed:
└─ agent\_world/main.py                    (# SYSTEMS WIRING sections only)
└─ agent\_world/core/systems\_manager.py
└─ agent\_world/systems/**init**.py        (if needed for imports)
Outline:
• Instantiate `SystemsManager` inside `bootstrap()`.
• Register systems *in deterministic order*:
PhysicsSystem → MovementSystem → PerceptionSystem → CombatSystem
→ Interaction systems (Pickup, Trading, Stealing, Crafting)
→ AbilitySystem → AIReasoningSystem → **ActionExecutionSystem** (new).
• Each tick: `systems_manager.update(world, tick)` **before**
`TimeManager.sleep_until_next_tick()`.

Task 17-A-2
Developer **@dev-alice**
Files allowed:
└─ agent\_world/core/components/force.py   (new)
└─ agent\_world/systems/ai/action\_execution\_system.py  (new)
Outline:
• `Force(dx:float, dy:float, ttl:int=1)` dataclass.
Helper: `apply_force(entity_id, dx, dy, ttl=1)` which attaches/accumulates.
• `ActionExecutionSystem` consumes `ActionQueue`, translating:
• `MoveAction` → `apply_force(dx,dy)` (ttl = 1)
• `AttackAction` → call `CombatSystem.attack()`.
• Remove any Velocity component after applying a force to avoid duplication.

Task 17-A-3
Developer **@dev-bob**
Files allowed:
└─ agent\_world/systems/movement/physics\_system.py
└─ agent\_world/systems/movement/movement\_system.py
└─ agent\_world/persistence/event\_log.py
Outline:
• **PhysicsSystem**: integrate `Force` each tick → update `Physics.vx/vy`.
If resulting move would hit `pathfinding.is_blocked()`, zero velocity and
append `{"type":"collision","entity":eid,"pos":(x,y)}` to `EventLog`.
• `MovementSystem` now queries the spatial index instead of raw loops,
and emits `"move_blocked"` events when a requested tile is occupied.

```

### Wave 17-B (2 parallel tasks)

```

Task 17-B-1
Developer **@dev-charlie**
Files allowed:
└─ agent\_world/core/world.py
└─ agent\_world/main.py   (# SPATIAL BOOTSTRAP only)
Outline:
• Create a `SpatialGrid(cell_size=1)` in `bootstrap()`.
• Populate it with existing entities (if any on load); update
MovementSystem & PickupSystem loops to use `spatial_index.query_radius()`.

Task 17-B-2
Developer **@dev-dana**
Files allowed:
└─ agent\_world/utils/observer.py
Outline:
• Warn once per run if any `[world].*_manager` is `None`.
• Add `observer.log_event("collision", {...})` and
`observer.log_event("move_blocked", {...})` helpers.

```

---

## Phase 18 · LLM Determinism & Test Harness
*Objective: predictable AI in CI and fast offline iteration.*

### Wave 18-S (​stub – merge **first**)  
Sets the public contract other tasks depend on.

```

Task 18-S-1
Developer **@dev-elliot**
Files:
└─ agent\_world/ai/llm/llm\_manager.py
└─ agent\_world/config.yaml
Outline:
• Add `llm.mode: ["offline", "echo", "live"]` (default **offline**) to YAML.
• `OFFLINE` ⇒ `"<wait>"`; `ECHO` ⇒ return last non-empty line; `LIVE` ⇒ current logic.
• `AW_LLM_MODE` env-var overrides YAML.
• Provide `LLMManager.current_mode()` helper used by tests.

```

### Wave 18-A (run **in parallel** after 18-S)

```

Task 18-A-1
Developer **@dev-fay**
Files:
└─ tests/conftest.py            (new)
└─ tests/test\_ai\_determinism.py (new)
Outline:
• Pytest fixture `mock_llm(mapping)` that monkey-patches
`LLMManager.request()` with table `{agent_id: reply}`.
• Integration test: two agents with scripted replies `{1:"MOVE N", 2:"ATTACK 1"}`,
run one tick, assert world state updated.

Task 18-A-2
Developer **@dev-glen**
Files:
└─ agent\_world/ai/angel/generator.py
└─ tests/test\_angel\_generator.py (new)
Outline:
• `generate_ability(desc, *, stub_code:str|None=None)` parameter; when supplied,
insert `stub_code` into `execute()`.
• Unit test writes a scaffold, hot-reloads via `AbilitySystem`, asserts
custom body executed.

```

---

## Phase 19 · Config & Memory Hygiene
*Objective: move magic numbers to YAML and cap in-memory growth.*

### Wave 19-A (**fully parallel**)

```

Task 19-A-1
Developer **@dev-hana**
Files:
└─ config.yaml
└─ agent\_world/utils/asset\_generation/sprite\_gen.py
Outline:
• Add section

```
cache:
  sprite_max: 10000      # max images in RAM
  log_retention_mb: 50   # event-log rotation
world:
  max_entities: 8000
```

• Implement LRU eviction for `_SPRITE_CACHE`.

Task 19-A-2
Developer **@dev-ian**
Files:
└─ agent\_world/persistence/event\_log.py
Outline:
• When current log exceeds `cache.log_retention_mb`, rotate to
`events_YYYYMMDD_HHMM.jsonl` and gzip the old file.

```

---

## Phase 20 · GUI Rendering + Input  
*Replace ASCII `/view` with hardware-accelerated window.*

### Wave 20-S (​stub – merge **first**)  

```

Task 20-S-1
Developer **@dev-alice**
Files:
└─ agent\_world/gui/window\.py   (new)
└─ agent\_world/gui/renderer.py (new)
└─ agent\_world/main.py         (# GUI HOOK only)
Outline:
• Define minimal interfaces:

```python
class Window:
    def draw_sprite(self, entity_id:int, x:int, y:int, pil_image): ...
    def draw_text(self, text:str, x:int, y:int, colour=(255,255,255)): ...
    def refresh(self): ...
class Renderer:
    def update(self, world): ...
```

• Add no-op implementations so downstream tasks can import & compile.
• Inject `renderer.update()` stub into main loop when
`state["gui_enabled"]` is true (toggle will arrive later).

```

### Wave 20-A (**parallel** after 20-S)

```

Task 20-A-1
Developer **@dev-alice**
Files:
└─ agent\_world/gui/window\.py
└─ pyproject.toml  (add `pygame`)
Outline:
• Replace stub with real `pygame` window (config-driven size, resizable).
• Maintain `self._sprite_cache: dict[int, pygame.Surface]`.
• Convert `PIL.Image` → `pygame.Surface` on first use.
• Implement `draw_sprite`, `draw_text`, `refresh`.

Task 20-A-2
Developer **@dev-bob**
Files:
└─ agent\_world/gui/renderer.py
└─ agent\_world/utils/observer.py
Outline:
• Iterate entities with `Position`; blit via `window.draw_sprite`.
• FPS overlay (average from `_tick_durations`).
• Camera centre, arrow-key pan, scroll-wheel zoom
(handle in `pygame.event.get()`).

Task 20-A-3
Developer **@dev-charlie**
Files:
└─ agent\_world/utils/cli/command\_parser.py
└─ agent\_world/utils/cli/commands.py
Outline:
• Add `/gui` command toggling `state["gui_enabled"]`.
• When enabled, wrap `TimeManager.sleep_until_next_tick`
to call `renderer.update(world)` then `window.refresh()`.

```

### Wave 20-B (after 20-A)

```

Task 20-B-1
Developer **@dev-dana**
Files:
└─ agent\_world/gui/input.py   (new)
└─ agent\_world/systems/ai/actions.py
Outline:
• Map left-click on an entity → enqueue `MOVE` or `ATTACK` for
“player controller” (entity 0).
• Hot-keys:
Space – pause/unpause
F     – toggle live FPS
R     – reload abilities
• Use existing `ActionQueue` to maintain determinism.

Task 20-B-2
Developer **@dev-elliot**
Files:
└─ agent\_world/utils/asset\_generation/sprite\_gen.py
Outline:
• Support `outline_colour` arg in `generate_sprite()`.
• GUI passes highlight colour for hovered/selected entities.
• Cache outlined variants separately.

---

## Phase 21 · Agent Autonomy Foundation
*Objective: Enable NPCs to act as autonomous agents driven by LLM decisions, and lay the groundwork for dynamic ability generation.*

### Wave 21-S (stub — merge first)

Task 21-S-1
Developer @dev-alice
Files allowed:
└─ agent_world/core/world.py
└─ agent_world/ai/llm/llm_manager.py
Outline:
• Add `llm_manager_instance: LLMManager | None = None` to `World` class.
• Add `async_llm_responses: dict[str, asyncio.Future[str]] = {}` to `World` to track pending LLM responses (key: unique prompt_id, value: Future).
• Add `llm_processing_thread: threading.Thread | None = None` to `World`.
• In `LLMManager`, modify `request()`:
    • If "live", generate a unique `prompt_id`.
    • Store an `asyncio.Future[str]` in `world.async_llm_responses[prompt_id]`.
    • Put `(prompt, world.async_llm_responses[prompt_id], prompt_id)` onto `self.queue`.
    • Return the `prompt_id` string instead of `"<wait>"`.
• Add `LLMManager.start_processing_loop(world_ref)`:
    • Creates and starts a new daemon thread.
    • This thread runs an `asyncio` event loop.
    • The `asyncio` loop continuously calls `await self.process_queue_item()`.
• Add `LLMManager.process_queue_item()` (async):
    • Gets `(prompt, future, prompt_id)` from `self.queue`.
    • **(Stub for now)**: Simulates an API call: `await asyncio.sleep(0.1); result = f"action_for_{prompt_id}"`.
    • Calls `future.set_result(result)`.
    • Puts `(prompt, result)` into `self.cache`.

Task 21-S-2
Developer @dev-bob
Files allowed:
└─ agent_world/core/components/ai_state.py
Outline:
• Add `pending_llm_prompt_id: str | None = None` to `AIState` dataclass.
• Add `last_llm_action_tick: int = -1` to `AIState` (to control LLM call frequency).

### Wave 21-A (parallel once Wave 21-S merged)

Task 21-A-1
Developer @dev-charlie
Files allowed:
└─ agent_world/main.py (bootstrap section)
└─ agent_world/utils/cli/commands.py (spawn command)
Outline:
• In `bootstrap()`:
    • Instantiate `LLMManager`.
    • Assign it to `world.llm_manager_instance`.
    • Call `world.llm_manager_instance.start_processing_loop(world)`.
• Modify `/spawn npc` command:
    • When an NPC is spawned, add an `AIState` component to it.
    • Initialize `AIState` with a default personality (e.g., "curious explorer") and empty goals.

Task 21-A-2
Developer @dev-dana
Files allowed:
└─ agent_world/systems/ai/ai_reasoning_system.py
Outline:
• Modify `AIReasoningSystem.update()`:
    • For each agent with `AIState`:
        • Check `world.time_manager.tick_counter > agent.ai_state.last_llm_action_tick + COOLDOWN_TICKS` (e.g., COOLDOWN_TICKS = 10) to limit LLM call frequency per agent.
        • If `agent.ai_state.pending_llm_prompt_id` is `None` (no pending request):
            • Build prompt.
            • Call `self.llm.request(prompt, world)` (LLMManager now needs world for `async_llm_responses`).
            • Store the returned `prompt_id` in `agent.ai_state.pending_llm_prompt_id`.
        • Else (if `pending_llm_prompt_id` exists):
            • Check `world.async_llm_responses[agent.ai_state.pending_llm_prompt_id].done()`.
            • If done:
                • Get result: `action_str = world.async_llm_responses.pop(agent.ai_state.pending_llm_prompt_id).result()`.
                • If `action_str` is not empty or `"<wait>"`:
                    • Add `(entity_id, action_str)` to `self.action_tuples_list` (the world's raw action list).
                    • Set `agent.ai_state.last_llm_action_tick = world.time_manager.tick_counter`.
                • Else (if result is bad or LLM still says wait), or if behavior tree is preferred on failure:
                    • Run behavior tree fallback: `fallback_action = self.behavior_tree.run(entity_id, self.world)`.
                    • If `fallback_action`: add `(entity_id, fallback_action)` to `self.action_tuples_list`.
                • Clear `agent.ai_state.pending_llm_prompt_id = None`.

Task 21-A-3
Developer @dev-elliot
Files allowed:
└─ agent_world/ai/llm/llm_manager.py
└─ pyproject.toml
Outline:
• **(This task assumes internet access for real API calls in dev, but CI will mock)**
• Add `httpx` and `aiohttp` to `pyproject.toml` (they are already there, verify versions if needed).
• Implement the actual OpenRouter API call in `LLMManager.process_queue_item()`:
    • Replace the `asyncio.sleep` stub with an `httpx.AsyncClient` POST request to OpenRouter.
    • Use `self.api_key` and `self.model`.
    • Handle potential `httpx.HTTPStatusError`, `httpx.RequestError` (network issues). If error, `future.set_result("<error_llm_call>")` or similar.
    • Parse the response to extract the action string.
• Ensure `LLMManager.offline` flag (based on `current_mode` and net check) correctly bypasses API calls in `process_queue_item`, setting future result to `"<wait>"` or echo behavior as per `self.mode`.

### Wave 21-B (serial follow-ups after Wave 21-A)

Task 21-B-1
Developer @dev-fay
Files allowed:
└─ agent_world/systems/ai/actions.py
└─ agent_world/systems/ai/action_execution_system.py
Outline:
• Define new action strings/parsing for:
    • `"LOG <message>"`: `LogAction(actor, message)` (prints to console for now).
    • `"IDLE"`: `IdleAction(actor)` (does nothing for a tick).
• Update `ActionExecutionSystem` to handle `LogAction` and `IdleAction`.
• Ensure `ActionExecutionSystem` gracefully handles unknown actions from LLM by logging a warning and treating it as IDLE.

Task 21-B-2
Developer @dev-glen
Files allowed:
└─ tests/test_ai_llm_integration.py (new)
└─ tests/conftest.py
Outline:
• Create `test_ai_llm_integration.py`.
• Add a pytest fixture in `conftest.py` `mock_openrouter_api(monkeypatch, responses: dict[str, str])` that patches `httpx.AsyncClient.post` to return canned responses based on prompt content or a sequence.
• Write an integration test:
    • Bootstrap world, spawn one NPC agent with `AIState`.
    • Use `mock_openrouter_api` to make the LLM return `"LOG test_message"`.
    • Run the simulation for a few ticks (e.g., AI reasoning cooldown + 1).
    • Assert that "test_message" was logged (e.g., by capturing stdout or checking a game event log if `LogAction` creates one).
    • Assert `agent.ai_state.pending_llm_prompt_id` is cleared and `last_llm_action_tick` is updated.

---

---

## Phase 22 · Angelic Intervention & Dynamic Ability Execution (Core Loop)
*Objective: Enable agents to request, generate, and use new abilities via the LLM and Angel system.*

### Wave 22-A: Action Definition & Parsing (Serial: 22-A-1 first)

Task 22-A-1
Developer @dev-root
Files allowed:
  └─ agent_world/systems/ai/actions.py
Outline:
  • Define `GenerateAbilityAction(actor, description: str)` dataclass.
  • Define `UseAbilityAction(actor, ability_name: str, target_id: Optional[int])` dataclass.
  • Update `Action` Union type to include these.
  • Modify `_parse_single_action_segment` in `actions.py`:
    • Add parsing for "GENERATE_ABILITY <description>" into `GenerateAbilityAction`.
    • Add parsing for "USE_ABILITY <ability_name> [target_id]" into `UseAbilityAction`. Ensure `target_id` is optional and correctly parsed as an int if present.

Task 22-A-2 (after 22-A-1)
Developer @dev-alice
Files allowed:
  └─ agent_world/systems/ai/actions.py (ActionQueue.enqueue_raw)
Outline:
  • Modify `ActionQueue.enqueue_raw` and `parse_action_string`:
    • When parsing LLM output like "LOG some message\nGENERATE_ABILITY heal self", ensure both `LogAction` and `GenerateAbilityAction` can be created and enqueued sequentially.
    • Similarly for "LOG ...\nUSE_ABILITY ...".
    • Ensure the primary action (GENERATE_ABILITY or USE_ABILITY) is prioritized if combined with LOG. (e.g. if "GENERATE_ABILITY ... \nLOG planning done", the GENERATE_ABILITY should happen). For simplicity, if LOG is first, allow subsequent MOVE/GENERATE/USE.

### Wave 22-B: Action Execution (Parallel once 22-A merged)

Task 22-B-1
Developer @dev-bob
Files allowed:
  └─ agent_world/systems/ai/action_execution_system.py
  └─ agent_world/ai/angel/generator.py (import only)
Outline:
  • Import `GenerateAbilityAction` and `UseAbilityAction`.
  • In `ActionExecutionSystem.update()`:
    • Handle `GenerateAbilityAction`:
        • Call `agent_world.ai.angel.generator.generate_ability(action.description)`.
        • Log an event or print to console: "Agent {actor_id} requested generation of ability based on description: '{action.description}'. File created: {path}".
    • Handle `UseAbilityAction`:
        • Access `world.systems_manager` to find the `AbilitySystem` instance (or assume `world.ability_system_instance` exists if set up in bootstrap).
        • Call `ability_system.use(action.ability_name, action.actor, action.target_id)`.
        • Log success or failure of the `use` call.

Task 22-B-2
Developer @dev-charlie
Files allowed:
  └─ agent_world/abilities/base.py
  └─ agent_world/abilities/builtin/melee.py
  └─ agent_world/abilities/builtin/ranged.py
Outline:
  • Update `Ability.execute` signature in `base.py` to `execute(self, caster_id: int, world: Any, target_id: Optional[int] = None)`.
  • Update `Ability.can_use` signature in `base.py` to `can_use(self, caster_id: int, world: Any, target_id: Optional[int] = None)`.
  • Update `MeleeStrike` and `ArrowShot` built-in abilities:
    • Modify their `execute` and `can_use` methods to match the new signature.
    • `MeleeStrike` might still auto-select a target if `target_id` is `None` but should use `target_id` if provided (and valid).
    • `ArrowShot` should primarily use `target_id` if provided, otherwise fallback to its current auto-targeting.

### Wave 22-C: System Integration & Angel Generator Refinement (Serial)

Task 22-C-1
Developer @dev-dana
Files allowed:
  └─ agent_world/main.py (bootstrap section)
  └─ agent_world/systems/ability/ability_system.py
Outline:
  • In `main.py bootstrap()`: Ensure `AbilitySystem` instance is created and accessible (e.g., `world.ability_system_instance = ability_system_instance` or ensure it's findable via `world.systems_manager.get_system(AbilitySystem)`).
  • In `AbilitySystem`:
    • Verify `_load_all()` is robust enough to pick up newly created files by `GenerateAbilityAction` during its regular `update()` call.
    • Add logging inside `_load_module` or `_register_module` when a new ability class is successfully loaded and instantiated.

Task 22-C-2
Developer @dev-elliot
Files allowed:
  └─ agent_world/ai/angel/generator.py
Outline:
  • Modify `generate_ability(desc, stub_code=None)`:
    • The `stub_code` in the generated ability's `execute` method should be a simple, universally applicable action, e.g., `print(f"Agent {user} used generated ability: {self.__class__.__name__} from description: {desc!r}")`.
    • Ensure the generated class name (e.g., from `_class_name(slug)`) is likely to be unique and usable as `ability_name` in `USE_ABILITY`. Perhaps append "Ability" if not already present.
    • The generated ability should have minimal `energy_cost = 0` and `cooldown = 1` (or some small default).

Task 22-C-3
Developer @dev-fay
Files allowed:
  └─ agent_world/ai/llm/prompt_builder.py
Outline:
  • Enhance the prompt's "Available Actions" section for `GENERATE_ABILITY` and `USE_ABILITY` with clear examples and syntax.
  • Add a specific instruction: "If you request an ability with GENERATE_ABILITY, in a subsequent turn, you can try to use it with USE_ABILITY <GeneratedAbilityClassName>."
  • Consider adding a small list of *currently known/learned abilities* to the prompt for the agent, so it knows what it can `USE_ABILITY`. This would require `AbilitySystem` to expose a list of available ability names for the agent. (For now, just improve instructions).

---

## Phase 23 · Agent Interaction & Ability Testing
*Objective: Test the end-to-end dynamic ability loop and observe more complex agent interactions.*

### Wave 23-A: Testing the Loop

Task 23-A-1
Developer @dev-root
Scenario:
  • Create a situation where an agent is "stuck" or has a clear need. E.g., place an item behind a conceptual "barrier" that it cannot pass.
  • Modify the agent's goals in `AIState` to "Acquire the item at [item_location]".
  • Observe if the LLM:
    1. Tries to move and fails.
    2. Logs its frustration or the obstacle.
    3. Attempts to `GENERATE_ABILITY` (e.g., "GENERATE_ABILITY phase through walls" or "GENERATE_ABILITY teleport to item").
    4. (After manual check of generated file) In a later turn, attempts to `USE_ABILITY <GeneratedAbilityName>`.
  • Document observations. No code changes expected in this task, purely an observation & scenario setup task.

Task 23-A-2
Developer @dev-alice
Files allowed:
  └─ tests/test_dynamic_abilities_integration.py (new)
  └─ tests/conftest.py
Outline:
  • Create an integration test similar to the scenario in 23-A-1 but automated.
  • Mock LLM responses:
    1. Initial exploration moves.
    2. A response: `GENERATE_ABILITY "SimplePrintAbility"`
    3. A response: `USE_ABILITY SimplePrintAbility`
  • In `conftest.py`, ensure the `GENERATED_DIR` for abilities is cleaned up before/after tests.
  • Assert:
    • The `SimplePrintAbility.py` file is created by the `GenerateAbilityAction`.
    • The `AbilitySystem` loads it.
    • The `UseAbilityAction` results in the stub code of `SimplePrintAbility` (e.g., a specific print message) being executed (capture stdout).

### Wave 23-B: Initial `PICKUP` and `ATTACK` Efficacy

Task 23-B-1
Developer @dev-bob
Files allowed:
  └─ agent_world/systems/ai/actions.py
  └─ agent_world/systems/ai/action_execution_system.py
  └─ agent_world/systems/interaction/pickup.py
Outline:
  • Implement `PickupAction(actor, item_id)` dataclass and parsing for "PICKUP <item_id>".
  • `ActionExecutionSystem`: Handle `PickupAction` by calling a new method `world.pickup_system_instance.pickup_item(actor_id, item_id)`. (Requires `PickupSystem` instance on world).
  • `PickupSystem`: Add `pickup_item(actor_id, item_id)` method.
    • Check if `actor_id` has `Position` and `Inventory`.
    • Check if `item_id` has `Position` and `Tag("item")`.
    • Check if they are at the same location.
    • If all true, move item to inventory and destroy item entity (or just remove its Position/Tag and add Ownership). Log success/failure.

Task 23-B-2
Developer @dev-charlie
Files allowed:
  └─ agent_world/ai/llm/prompt_builder.py
Outline:
  • When an item is visible in `visible_entities`, add a stronger hint to the LLM: "You see item <id> at <pos>. If it's useful for your goals, consider using `PICKUP <id>`."
  • When an NPC is visible: "You see NPC <id> at <pos>. Consider `LOG` its presence or `ATTACK <id>` if it aligns with your goals or if it appears hostile."
  • Test with scenarios where agents have goals to collect specific items or confront other NPCs.