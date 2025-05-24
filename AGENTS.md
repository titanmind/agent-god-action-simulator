# AGENTS.md – Working with the Agent World Simulator Repo

Welcome, Codex agents!
This document tells you **where you may edit, how to run code, and the ground rules that keep merges conflict-free**.

---

## 1. Repository Overview

*Project architecture subject to change
```
Agent World Simulator is a Python-only sandbox that fuses a lightweight ECS, LLM-driven agents, and procedural assets into an emergent, single-machine world. The repo is intentionally minimal—no containers, brokers, or external art—so you can iterate fast and keep everything hackable.

agent_world/
├── core/           # World, ECS storage
├── systems/        # Movement, combat, AI, abilities
├── ai/             # LLM manager, prompt builder, angel generator
├── abilities/      # base.py + generated/ hot-reload folder
├── persistence/    # save_load.py, event_log.py
├── utils/          # sandbox, CLI, observer, asset_gen
└── main.py         # entry point
```

No external art: all textures/sprites are procedurally generated under `assets/`.

---

## 2. Development Workflow

1. **If you are assigned a task from DEV_PLAN.md:** ensure you check off your task, wave, or phase when you complete your task.
2. **Create a branch** named `task/<phase>-<wave>-<id>`.
3. **Edit *only* the files listed for your task.**
4. Run `pytest` locally **early and often**; add/extend tests for every major update ([edbennett.github.io][1], [Real Python][2]).
5. `python main.py` must tick at 10 Hz with no traceback.
6. Commit with message `TASK <id>: <summary>` and open a PR.
7. Need a file outside your list? Open an issue—**do not edit unowned files.**

---

## 3. Coding & Modular-Architecture Standards

* Python ≥ 3.11, `black` formatting, type hints where practical.
* Avoid global state except the `entities` and `world` singletons in `core`.
* Keep imports lightweight—stdlib + the pip libs from the setup script.
* **Maintain a modular architecture.** When any file approaches **300 lines**, split it into focused sub-modules; plan ahead for files you expect to grow large ([The Hitchhiker's Guide to Python][3], [LabEx][4], [3D Slicer Community][5]).
* Use clear, lowercase module names and dodge circular imports ([The Hitchhiker's Guide to Python][3], [LabEx][4]).
* No new third-party packages without maintainer approval.

---

## 4. LLM Usage

* All OpenRouter calls flow through `ai/llm_manager.py`.
* API key comes from `OPENROUTER_API_KEY` (exported in the setup script).
* Prompts capped at **8 k tokens**; the manager enforces caching and timeouts.
* For deterministic replay, **log every prompt/response** via `event_log.py`.

---

## 5. Dynamic Abilities

* Generated abilities **must live in `abilities/generated/`** and subclass `abilities.base.Ability`.
* Use the hot-reload helper—no import hacks elsewhere.
* All ability code runs inside `utils.sandbox.run_in_sandbox()` and may touch the world only through the public `World` API.

---

## 6. CLI & Debugging

During development you can type commands into Codex’s terminal:

```
/pause              # stop the tick loop
/step               # advance one tick
/save               # force JSON snapshot
/reload abilities   # hot-reload newly generated code
/profile 5          # run 5-tick cProfile dump (std-lib, nothing to install)
```

---

## 7. Merge-Conflict Etiquette

* Never re-format files you don’t own.
* Rebase onto `main` before final push.
* Conflicts? Ping the other developer in your PR comments.

---

## 8. Contact & Support

* Lead maintainer: **@dev-root**
* Coding questions: tag **#engineering** in project chat.
* Environment issues (packages, API keys): tag **#infra**.
