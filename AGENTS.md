# AGENTS.md — General Contributor Handbook

This short guide explains how autonomous coding agents collaborate on any
repository that follows the **DEV_PLAN.md** process.

---

## 1 · Find Your Task

* Open **DEV_PLAN.md** (root of the repo).  
* If you are assigned a task, you will find it here, as well as sorrounding context for better understanding of your place within the DEV_PLAN flow.

---

## 2 · Understand the Project

* Open **PROJECT_DESIGN.md** (root of the repo).  
* Here you will find the overall project design notes, to give you more context of the entire project and what the finished version looks like.  This is the ideal we are constantly building towards.

---

## 3 · Edit Only Allowed Files

Each task lists its **Files allowed**.  
Touch **nothing else** – this prevents merge clashes with up to nine other
parallel agents.

---

## 4 · Local Workflow

2. Repo-specific entry point must run without traceback.  
3. Commit message format:

`TASK <phase>-<wave>-<tag>: <concise summary>`

4. Push and open a PR when the task is complete.

---

## 5 · Surfacing Blockers

You **cannot** open GitHub issues.  
If you must modify an out-of-scope file or hit any critical blocker:

1. **Stop coding.**  
2. Post a chat message titled  

```

BLOCKER <phase>-<wave>-<task>

```

3. Briefly describe what you need (extra file access, unclear spec, etc.).  
4. Wait for instructions – do **not** create a partial PR.

---

## 6 · Merge-Conflict Etiquette

* Never re-format someone else’s file.  
* Always rebase (`git pull --rebase origin main`) before pushing.  
* If a conflict appears, fix only your own lines.

---

## 7 · Deterministic LLM & Tests

ALWAYS SET PYTHON PATH BEFORE RUNNING TESTS

* The default configuration sets `llm.mode = offline`.
* **Two test tiers**  
  1. **Core / Unit** – must pass (`pytest -q tests/core tests/systems`).  
  2. **Integration / LLM / Network** – marked `@pytest.mark.integration`; **skipped** when
     `llm.mode == "offline"` or missing third-party packages.  
* When you add a new test that contacts the internet or needs extra deps, decorate it:

  ```python
  import pytest, os
  skip_offline = pytest.mark.skipif(
      os.getenv("NO_NET", "1") == "1",
      reason="Skipped in offline CI"
  )

  @skip_offline
  def test_my_cloud_thing(): ...
  ```

* Local smoke-check:  
  `pytest -q tests/core tests/systems`  
  Full suite (`pytest -q`) is **not required** in the sandbox image.

---

## 8 · Coding Standards

* Split any file approaching **300 LOC** – keep modules focused.  
* Prefer std-lib; add third-party packages if your task explicitly
says “add `<pkg>` to `pyproject.toml`”, OR if you determine there is a more efficient/best practice method not being utilized.  In such cases, you should stop coding and send a BLOCKER message
* Use type hints where practical.

---