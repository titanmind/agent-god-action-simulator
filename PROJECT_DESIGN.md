## Agent World Simulator — Project Design Document (v5)

*For the implementation schedule & task breakdown see **DEV\_PLAN.md***

---

### 0 · Snapshot

A **Python-only, single-process sandbox** that marries a lightweight ECS, async LLM-driven agents, deterministic replay and wholly-procedural art.
Nothing to download, no containers, no micro-services – just run `python main.py`.

---

## 1 · Core Philosophy

* **Self-hosted hobby project** – skip enterprise-grade ops.
* **Monolith over micro-services** – one interpreter, multiple threads / async tasks.
* **Procedural everything** – sprites, maps, items; zero external assets.
* **Deterministic by default** – CI runs with `llm.mode: offline`; unit-tests monkey-patch LLM replies.
* **Test-driven, modular** – ≥ 95 % pytest coverage; split any file ≥ ≈ 300 LOC.
* **Practical > perfect** – always ship a playable build before polishing.

---

## 2 · Runtime Architecture

```
main.py
├── Main Tick Loop (sync)
│   ├─ SystemsManager.update()
│   │   ├─ PhysicsSystem
│   │   ├─ ActionExecutionSystem     ← consumes parsed MOVE/ATTACK/… actions
│   │   └─ … others …
│   └─ observer.record_tick()
├── GUI Thread / Tick Hook  (pygame)
│   ├─ Window.refresh()
│   └─ Renderer.update(world)
├── LLM Worker Pool (asyncio)          up to 8 concurrent completions
├── Path-finding Pool                  optional CPU workers for A*
├── Persistence Task                   snapshot every 60 s + incremental deltas
└── Angel Task                         on-demand ability generation
```

*Soft budget* 100 ms per tick; overruns are logged by `observer`.

---

## 3 · LLM Integration

| Mode        | Description                                   | Config / Env                           |
| ----------- | --------------------------------------------- | -------------------------------------- |
| **offline** | Returns `"<wait>"` (CI default)               | `llm.mode: offline`                    |
| **echo**    | Echoes the last non-empty line of prompt      | `llm.mode: echo` or `AW_LLM_MODE=echo` |
| **live**    | Real OpenRouter call (falls back if net down) | `llm.mode: live`                       |

* Prompt pipeline:
  `world_view → prompt_builder → llm_manager.request() → action parsing → ActionQueue`.

* Determinism: every `{prompt, completion}` is appended to `event_log.jsonl`.
  Tests use `tests.conftest::mock_llm` to script replies per `agent_id`.

---

## 4 · ECS Core

### 4.1 Components (*canonical subset*)

```
position.py        (x, y)
physics.py         (vx, vy, mass, friction)
force.py           (dx, dy, ttl)          # consumed each tick by PhysicsSystem
health.py          (cur, max)
inventory.py       (capacity, items)
ai_state.py        (personality, goals)
perception_cache.py(visible, last_tick)
ownership.py       (owner_id)
relationship.py    (faction, reputation)
```

### 4.2 Managers & Index

* `EntityManager` – id → component-dict
* `ComponentManager` – registration / add / remove helpers
* `SpatialGrid` (hash grid, cell\_size 1); `Quadtree` wrapper for big worlds

---

## 5 · Gameplay Systems (deterministic order)

```
systems/
├ movement/            MovementSystem, pathfinding.py
├ physics/             PhysicsSystem                 ← integrates forces & velocity
├ action/              ActionExecutionSystem         ← sets Velocity or Force
├ perception/          PerceptionSystem, LOS helpers
├ combat/              CombatSystem, defense.py
├ interaction/         pickup.py, trading.py, stealing.py, crafting.py
├ ai/                  ai_reasoning_system.py, behaviour_tree.py
└ ability/             ability_system.py, cooldowns.py
```

`SystemsManager.update()` walks this list each tick.

---

## 6 · GUI & Input (pygame)

* **Window** – opens a resizable window, caches `pygame.Surface` per sprite.
* **Renderer** – draws all entities with `Position` + optional overlays (FPS, selection outlines, hit pop-ups).
* **Input** – mouse picks entities; hotkeys: **Space** pause, **F** FPS overlay, **R** hot-reload abilities.
* **Sprites** – 32 × 32 PNGs from `utils/asset_generation/sprite_gen.py`; outlined variants cached with separate keys.

---

## 7 · LLM-Generated Abilities & Sandbox

* Base class `abilities.base.Ability` (`can_use`, `execute`, `energy_cost`, `cooldown`).
* **Angel generator** writes scaffolds to `abilities/generated/*.py`.
* **RestrictedPython** sandbox, 50 ms CPU, import-whitelist `{"math"}`.
* Hot-reload each tick; cooldowns tracked per entity.

---

## 8 · Persistence & Replay

* **Full snapshot** – `save_load.py` → `world_state.json.gz`.
* **Incremental deltas** – `incremental_save.py` every 5 ticks; diff & gzip.
* **Event log** – JSONL stream (`tick, type, data`); auto-rotated when size exceeds `cache.log_retention_mb`.
* **Replay** – feeds events into fresh world; asserts deterministic equality.

---

## 9 · Observability & CLI

* `observer` keeps a rolling deque of 1 000 tick durations; prints FPS on demand.
* CLI commands (non-blocking stdin):
  `/pause  /step  /save  /reload abilities  /profile N  /gui  /fps  /spawn …`

GUI & CLI both enqueue into `ActionQueue` to keep the simulation deterministic.

---

## 10 · Procedural Asset Generation & Caches

* `sprite_gen.py` – colour from `entity_id`, HSV→RGB palettes per faction, optional outline.
* LRU sprite cache (size from `cache.sprite_max`).
* White-noise & Perlin helpers in `asset_generation/noise.py` seed resource nodes.

---

## 11 · Testing & Determinism

* Pytest suites in `tests/`; CI runs with `llm.mode: offline`.
* Fixtures in `tests/conftest.py` provide mock LLM replies and force deterministic timeouts.
* End-to-end smoke test: spawn a world, run ≥ 5 ticks, assert at least one entity moved/injured, snapshot & replay.

---

## 12 · Configuration Skeleton (`config.yaml`)

```yaml
world:
  size:            [100, 100]
  tick_rate:       10
  max_entities:    8000

llm:
  mode:            offline        # offline | echo | live
  provider:        openrouter
  model:           openai/gpt-4o
  max_concurrent:  8
  timeout:         2.0

window:
  size:            [800, 600]

cache:
  sprite_max:      10000          # in-RAM sprite surfaces
  log_retention_mb: 50            # rotate event logs when bigger

paths:
  saves:           "./saves"
  abilities:       "./abilities/generated"
```

---

### 13 · Roadmap Alignment

*Phase 0-16 delivered the ECS, physics, LLM hooks & CLI.*
*Phase 17 → 21 (see DEV\_PLAN.md) add deterministic LLM modes, config hygiene, pygame GUI, input → ActionQueue, and final docs/tests.*
