Below is a **phased, wave-based build roadmap** designed for a single-repo, Python-only project.
*Every task is self-contained, names the exact files that may be touched, and assigns one developer handle.*
Follow the waves in order; do **not** start a later wave until all tasks in the current wave have merged cleanly.
Remember: **no external art or assets** – everything visual will later be generated procedurally.


---

## Phase 1 · Core Skeleton

### Wave 1-A  (3 parallel tasks)

```
Task 1-A-1
Developer @dev-alice
Files allowed to edit:
  └─ agent_world/core/world.py
Task outline:
  • Define `World(size)` class with `tiles` dict and simple `add_entity`, `remove_entity` stubs.
  • No game logic yet.
Reinforcement:
  - Keep imports limited to stdlib.

Task 1-A-2
Developer @dev-bob
Files allowed to edit:
  └─ agent_world/core/components.py
Task outline:
  • Create dataclass shells: Position, Health, Inventory, AIState.
  • Each only holds data; no methods beyond `__repr__`.
Reinforcement:
  - Do NOT reference World or other modules.

Task 1-A-3
Developer @dev-charlie
Files allowed to edit:
  └─ agent_world/core/entities.py
Task outline:
  • Implement `create_entity(components: dict) -> entity_id`.
  • Maintain global `entities` dict.
  • Provide `get_component(entity_id, comp_name)`.
Reinforcement:
  - Do not introduce game rules; pure storage.
```

### Wave 1-B  (2 parallel tasks, after 1-A merged)

```
Task 1-B-1
Developer @dev-dana
Files allowed to edit:
  └─ agent_world/core/time_manager.py
Task outline:
  • Implement `TimeManager` with tick_rate, tick_counter, `sleep_until_next_tick`.
  • Unit-test in same file under `if __name__ == "__main__":`.
Reinforcement:
  - No asyncio yet; blocking sleep only.

Task 1-B-2
Developer @dev-elliot
Files allowed to edit:
  └─ agent_world/main.py
Task outline:
  • Wire minimal main loop: create World, TimeManager, iterate 10 ticks printing tick number.
Reinforcement:
  - Import ONLY modules created in Phase 1.
```

---

## Phase 2 · Base Systems

### Wave 2-A  (3 parallel tasks)

```
Task 2-A-1
Developer @dev-fay
Files allowed to edit:
  └─ agent_world/systems/movement_system.py
Task outline:
  • Function `movement_system(world)` moves entities with Position and Velocity component (Velocity dataclass lives here).
  • Update spatial grid in world.
Reinforcement:
  - No collision logic yet.

Task 2-A-2
Developer @dev-glen
Files allowed to edit:
  └─ agent_world/systems/spatial_index.py
Task outline:
  • Build `SpatialGrid(cell_size=1)` with `insert`, `query_radius`.
  • Integrate into World via composition (World holds grid instance).
Reinforcement:
  - Do not modify other files.

Task 2-A-3
Developer @dev-hana
Files allowed to edit:
  └─ agent_world/systems/perception_system.py
Task outline:
  • Scan nearby entities via SpatialGrid; add list of visible entity IDs to a new component `PerceptionCache`.
Reinforcement:
  - Read-only access to World; no side effects besides cache.
```

### Wave 2-B  (2 parallel tasks, after 2-A)

```
Task 2-B-1
Developer @dev-ian
Files allowed to edit:
  └─ agent_world/systems/combat_system.py
Task outline:
  • If two entities are both in range 1 and hostile flag is set, subtract 10 health.
  • Emit simple print log “X hit Y”.
Reinforcement:
  - No death handling yet.

Task 2-B-2
Developer @dev-jade
Files allowed to edit:
  └─ agent_world/systems/interaction_system.py
Task outline:
  • Implement pickup: if entity with Inventory stands on item entity, move item ID into inventory list.
Reinforcement:
  - No trade/steal yet.
```

---

## Phase 3 · LLM Integration

### Wave 3-A  (2 parallel tasks)

```
Task 3-A-1
Developer @dev-alice
Files allowed to edit:
  └─ agent_world/ai/llm_manager.py
Task outline:
  • Implement `LLMManager.request(prompt: str) -> str` using stubbed fake response `"<wait>"`.
  • Include async `asyncio.Queue` with maxsize 128.
Reinforcement:
  - No real API calls; placeholder only.

Task 3-A-2
Developer @dev-bob
Files allowed to edit:
  └─ agent_world/ai/prompts.py
Task outline:
  • Provide `build_prompt(agent_id, world_view)` that returns deterministic string for now.
Reinforcement:
  - Pure function, no side effects.
```

### Wave 3-B  (1 task, after 3-A)

```
Task 3-B-1
Developer @dev-charlie
Files allowed to edit:
  └─ agent_world/systems/ai_reasoning_system.py
  └─ agent_world/main.py  (only inside the "# AI hook" region)
Task outline:
  • Iterate over agents each tick, put prompt on LLMManager queue, fetch response with 0.05 s timeout, fallback to 'wait'.
  • Translate 'move N' or 'attack' string into action queued on entity.
Reinforcement:
  - Edit only the marked hook in main.py.
```

---

## Phase 4 · Persistence & Replay

### Wave 4-A  (2 parallel tasks)

```
Task 4-A-1
Developer @dev-dana
Files allowed to edit:
  └─ agent_world/persistence/save_load.py
Task outline:
  • `save_world(world, path)` and `load_world(path)` writing JSON to disk.
  • Compress with gzip if file ends “.gz”.
Reinforcement:
  - No incremental saves yet.

Task 4-A-2
Developer @dev-elliot
Files allowed to edit:
  └─ agent_world/persistence/event_log.py
Task outline:
  • Append JSONL lines: {tick, event_type, data}.
  • Provide `replay(events_path, start_tick, end_tick)` yields event dicts.
Reinforcement:
  - Event types confined to strings already used in systems.
```

### Wave 4-B  (1 task, after 4-A)

```
Task 4-B-1
Developer @dev-fay
Files allowed to edit:
  └─ agent_world/main.py  (inside "# Persistence hook" block only)
Task outline:
  • Call save_world every 60 s.
  • On startup, if latest save exists, load it; else fresh world.
Reinforcement:
  - Touch no other parts of main loop.
```

---

## Phase 5 · Dynamic Abilities & Sandboxing

### Wave 5-A  (2 parallel tasks)

```
Task 5-A-1
Developer @dev-glen
Files allowed to edit:
  └─ agent_world/abilities/base.py
  └─ agent_world/utils/sandbox.py
Task outline:
  • Implement `Ability` base class with `can_use`/`execute`.
  • Provide `run_in_sandbox(code_str)` via RestrictedPython, 50 ms timeout.
Reinforcement:
  - Sandbox must deny `import` except `math`.

Task 5-A-2
Developer @dev-hana
Files allowed to edit:
  └─ agent_world/ai/angel.py
Task outline:
  • Stub `generate_ability(description)` that writes a new `.py` file into `abilities/generated/` with minimal `Ability` subclass template.
Reinforcement:
  - No real LLM yet; fake code with pass statements.
```

### Wave 5-B  (1 task, after 5-A)

```
Task 5-B-1
Developer @dev-ian
Files allowed to edit:
  └─ agent_world/systems/ability_system.py
Task outline:
  • On tick, iterate entities with queued ability names, import module with hot-reload helper, run `execute`.
  • Handle cooldown tracking per entity.
Reinforcement:
  - Abilities may only modify world through public APIs.
```

---

## Phase 6 · Debug CLI & Observability

### Wave 6-A  (2 parallel tasks)

```
Task 6-A-1
Developer @dev-jade
Files allowed to edit:
  └─ agent_world/utils/observer.py
Task outline:
  • Implement `WorldObserver.dump_state('state_dump.json')`.
  • Rolling tick duration deque and simple `print_fps()`.

Task 6-A-2
Developer @dev-root
Files allowed to edit:
  └─ agent_world/utils/cli.py
  └─ agent_world/main.py  (inside "# CLI hook" only)
Task outline:
  • Provide `/pause`, `/step`, `/save`, `/reload abilities`, `/profile 5` commands read from stdin.
  • Integrate into main loop non-blocking using `select`.
```

---

## Phase 7 · Procedural Asset Generation (future polish)

### Wave 7-A  (1 task)

```
Task 7-A-1
Developer @dev-alice
Files allowed to edit:
  └─ agent_world/utils/asset_gen.py
  └─ assets/  (new folder)
Task outline:
  • Generate simple 32×32 PNG sprite sheets procedurally with Pillow: solid color + agent ID text.
  • Provide `get_sprite(entity_id)` returning PIL.Image.
Reinforcement:
  - No external files downloaded.
```

---

### Completion criteria

* All phases merged without file-scope collisions.
* Game runs with `python main.py`, ticks at 10 Hz, saves/restores, agents move/attack, abilities hot-reload, and basic CLI works.

Stick to the file boundaries above; if you **must** touch another file, raise a merge-blocker issue instead of editing directly. Happy coding!
