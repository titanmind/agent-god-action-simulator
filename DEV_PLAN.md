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

### Completion Criteria

* All phases merged without file-scope conflicts.
* `python main.py` runs at 10 Hz, saves/restores state, agents move & fight, abilities hot-reload, CLI commands work.
* Every major PR ships or updates **pytest** coverage; CI green before merge.

Stay within your file boundaries; open a merge-blocker issue if another file must change. Happy hacking!


