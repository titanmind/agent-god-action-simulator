## Agent World Simulator — Project Design Document (v4)

### Summary

Agent World Simulator is a **Python-only, single-process sandbox** that combines a lightweight ECS, async OpenRouter-driven agents, and wholly procedural art to create an emergent, self-hosted world. The codebase is rigorously modular: any file that approaches **≈300 LOC must be split**. No external art, no micro-services, no container stack—just run `python main.py`.

---

## 1 · Core Philosophy

* **Self-hosted hobby project** — skip enterprise security/compliance.
* **Monolith over micro-services** — one interpreter, multiple threads/async tasks.
* **Procedural everything** — sprites, maps, items; nothing downloaded.
* **Test-driven & modular** — thorough pytest coverage; files ≥300 LOC must be factored.
* **Practical > perfect** — ship playable builds, iterate quickly.

---

## 2 · Runtime Architecture

### 2.1 Thread & Task Layout

```
main.py
├── Main Loop (sync): tick, physics, system dispatch
├── LLM Worker Pool (asyncio tasks): up to 8 concurrent completions
├── Path-finding Pool  : optional CPU workers for A*
├── Persistence Task   : snapshot every 60 s
└── Angel Task         : on-demand ability generation
```

### 2.2 Time Manager

* `tick_rate` (default 10 Hz)
* `tick_counter` (global)
* `sleep_until_next_tick()` maintains target cadence.
* **Soft budget** 100 ms; overruns recorded by `observer.print_fps()`.

### 2.3 LLM Latency Policy

* Each agent gets **50 ms** to respond.
* On timeout: cached/default action.
* Late replies applied next tick; agent marked *thinking* meanwhile.

---

## 3 · ECS Core

### 3.1 Entity Storage

* `EntityManager` holds `entity_id → component_dict`.
* `ComponentManager` tracks registered component types.

### 3.2 Canonical Components

```
core/components/
│ position.py        (x, y)
│ physics.py         (velocity, mass)
│ health.py          (cur, max)
│ inventory.py       (capacity, items)
│ ai_state.py        (personality, goals)
│ perception_cache.py(visible, last_tick)
│ ownership.py       (owner_id)
│ relationship.py    (faction, reputation)
```

### 3.3 Spatial Index

* `SpatialGrid` (hash grid, cell\_size 1) for common queries.
* `Quadtree` optional drop-in for larger maps.

---

## 4 · Gameplay Systems

```
systems/
├ movement/        (movement_system.py, pathfinding.py)
├ perception/      (perception_system.py, line_of_sight.py)
├ combat/          (combat_system.py, damage_types.py, defense.py)
├ interaction/     (pickup.py, trading.py, stealing.py, crafting.py)
├ ai/              (ai_reasoning_system.py, behavior_tree.py, actions.py)
└ ability/         (ability_system.py, cooldowns.py)
```

Systems run in deterministic order via `core/systems_manager.py`.

---

## 5 · LLM Integration

### 5.1 OpenRouter Manager

* `ai/llm/llm_manager.py`

  * Async queue (max 128).
  * LRU cache (1 k prompts).
  * Back-off & retry.

### 5.2 Prompt Pipeline

```
world_view → prompt_builder.py → llm_manager.request() 
             → raw completion → actions.parse() → action queue
```

### 5.3 Determinism

* Every `{prompt, completion}` appended to `event_log.jsonl`; replays bypass API.

---

## 6 · Dynamic Abilities & Sandbox

* Base class `abilities/base.py` (`can_use`, `execute`, `energy_cost`, `cooldown`).
* Angel generator writes Python modules to `abilities/generated/`.
* `utils/sandbox.py` executes code under **RestrictedPython**, 50 ms CPU, `math`-only imports.
* `systems/ability/ability_system.py` hot-reloads modules each tick and enforces cooldowns.

---

## 7 · Persistence & Replay

* **Snapshots** — `save_load.py` dumps `world_state.json.gz`.
* **Incrementals** — `incremental_save.py` delta-compresses every 5 ticks.
* **Event Log** — `event_log.py` streams JSONL: `tick, event_type, data`.
* **Replayer** — `replay.py` feeds events back to the engine for verification.

Folder layout:

```
saves/
└─ world_001/
   ├─ world_state.json.gz
   ├─ events/0000000-0005000.jsonl
   └─ memories/agent_042.json   (optional)
```

---

## 8 · Observability & CLI

### 8.1 Observer

* Rolling tick durations (`deque`, length 1000).
* FPS/LLM latency printouts.
* `dump_state(path)` for offline inspection.

### 8.2 CLI Commands (`utils/cli`)

```
/pause, /step, /save, /reload abilities, /profile N, /spawn, /debug <id>
```

Non-blocking stdin read via `select`.

---

## 9 · Procedural Asset Generation

* `utils/asset_generation/sprite_gen.py` — 32 × 32 PNG, HSV palette per faction, ID text overlay.
* `get_sprite(entity_id)` caches `PIL.Image` objects in memory.

No external textures—the game generates everything on demand.

---

## 10 · Testing & Modularisation

* **pytest** suites in `tests/`; CI must stay green.
* Any file ≥300 LOC must be split **immediately**—open a refactor PR if you breach.
* Plan module growth: create sub-packages (`movement/`, `combat/`) early to avoid churn.

---

## 11 · Folder Map (high-level)

```
agent_world/
├ core/                  # world, managers, components, spatial
├ systems/               # movement, perception, combat, etc.
├ ai/                    # llm, angel, prompt builder
├ abilities/             # base, builtin, generated/
├ persistence/           # save load, replay, event log
├ utils/                 # sandbox, observer, cli, profiling, assets
└ main.py
assets/                  # runtime-generated sprites
tests/                   # pytest suites
config.yaml
```

---

## 12 · Configuration Example

```yaml
world:
  size: [100, 100]
  tick_rate: 10

llm:
  provider: "openrouter"
  model: "openai/gpt-4o"
  max_concurrent: 8
  timeout: 2.0

paths:
  saves: "./saves"
  abilities: "./abilities/generated"
```

---

## 13 · Getting Started

```bash
pip install -r requirements.txt       # PyYAML aiohttp httpx RestrictedPython Pillow pytest openrouter-selector
export OPENROUTER_API_KEY="your_key"
python main.py
```

---

### Roadmap Alignment

This design pairs 1-to-1 with **DEV\_PLAN.md**: each phase populates the modules outlined here, keeping file sizes manageable and tests green.
