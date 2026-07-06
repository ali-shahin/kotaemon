# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **TODO list:** the project's task list (TODO / BACKLOG / PLANNING / DONE) lives at `.local/tasks.md`.

## Workflow

When implementing a feature or fixing a bug, prefer working off a dedicated git
worktree (one per feature/bug) so multiple efforts can proceed in parallel
without interfering.

## Overview

Kotaemon is an open-source RAG UI for chatting with documents. It is both a reusable
library for building RAG pipelines and a full Gradio web application built on top of it.

## Monorepo layout (uv workspace)

This is a `uv` workspace (`tool.uv.workspace` in the root `pyproject.toml`) with two
installable packages plus a thin top-level launcher:

- `libs/kotaemon/` — package `kotaemon`: the **core library**. Provider-agnostic building
  blocks for RAG: `llms/`, `embeddings/`, `rerankings/`, `loaders/`, `indices/` (retrievers,
  rankings, splitters, ingests, qa, vectorindex), `storages/` (doc stores & vector stores),
  `agents/`, `parsers/`. No UI, no app state.
- `libs/ktem/` — package `ktem`: the **application** (`ktem`). A Gradio app that composes
  `kotaemon` components into user-facing features. Holds UI `pages/`, the `index/` system,
  `reasoning/` pipelines, `db/` (SQLAlchemy/sqlmodel), `mcp/`, and app/state plumbing.
- Root `app.py` — entrypoint. Reads `flowsettings.py`, builds `ktem.main.App`, launches Gradio.

`kotaemon` knows nothing about `ktem`; `ktem` depends on `kotaemon`. Keep that direction.

## Core architecture concepts

**Everything is a `BaseComponent` (theflow).** `kotaemon.base.BaseComponent` subclasses
`theflow.Function`. A "pipeline" is just a component that nests other components. To build one:
subclass `BaseComponent`, declare init params and nodes as typed class attributes (an attribute
typed as a `BaseComponent` subclass becomes a "node"), and implement `run()`. Components are
callable and support caching/logging/visualization. See `docs/development/create-a-component.md`.
A component should tolerate multiple input types (str / Document / lists) but emit a single,
generic output type — usually `Document` from `kotaemon.base.schema`.

**Indices** (`ktem.index.base.BaseIndex`) are the app's pluggable storage+retrieval units. An
index defines its DB tables / vector store, its admin & user settings, its indexing pipeline
(`get_indexing_pipeline`), and its retriever pipelines (`get_retriever_pipelines`), plus the
Gradio UI to manage and select it. The default file index lives in `libs/ktem/ktem/index/file/`;
GraphRAG variants (MS GraphRAG, NanoGraphRAG, LightRAG) live under `index/file/graph/`.

**Reasoning pipelines** (`libs/ktem/ktem/reasoning/`) turn a question + retrieved context into an
answer. `simple.py` holds the default `FullQAPipeline` / `FullDecomposeQAPipeline`; `react.py` and
`rewoo.py` are agent-based. They are registered in `flowsettings.py` as `KH_REASONINGS`.

**UI is composed from `BasePage` objects.** `ktem.main.App` (subclass of `ktem.app.BaseApp`)
follows a lifecycle: render UI → declare public events → subscribe → register events. Each tab is
a `BasePage` in `ktem/pages/` (chat, settings, resources, login, setup).

**Configuration is `flowsettings.py`**, read via `theflow.settings` and `python-decouple`
(env vars / `.env`). All app config constants are prefixed `KH_` (e.g. `KH_DOCSTORE`,
`KH_VECTORSTORE`, `KH_LLMS`, `KH_REASONINGS`, `KH_INDICES`). The `.env` file only seeds the DB on
first run; afterward configuration lives in the DB and is editable in the UI. Runtime app data
(SQLite DB, files, caches) lives in `./ktem_app_data/`.

## Common commands

Environment setup (Python >= 3.11):

```shell
uv sync --python 3.11          # install workspace (recommended)
source .venv/bin/activate
# or, without uv:
pip install -e "libs/kotaemon[all]" && pip install -e "libs/ktem"
```

Run the app (defaults to user/pass `admin`/`admin`, opens browser):

```shell
python app.py
```

Run with Docker Compose (builds the `lite` image from the local `Dockerfile`):

```shell
cp .env.example .env        # optional: seed model config on first run, then edit keys
docker compose up --build   # build + start; UI at http://localhost:7860 (admin/admin)
docker compose up -d        # run detached
docker compose down         # stop
```

App data persists on the host in `./ktem_app_data/`. To use a heavier variant, change
`target:` in `docker-compose.yml` from `lite` to `full` or `ollama` (matches the
`Dockerfile` stages).

Lint / format (must pass in CI). Config in `.pre-commit-config.yaml`: black, isort (black
profile), flake8 (max-line-length 88, ignore E203), autoflake, prettier, mypy, codespell.

```shell
pre-commit run --all-files
```

Tests — the two packages have separate suites. `libs/kotaemon/pytest.ini` sets `testpaths = tests`,
so run pytest from within the package dir (or pass the path):

```shell
pytest libs/kotaemon/tests/               # core library tests
pytest libs/ktem/ktem_tests/              # app tests
pytest libs/kotaemon/tests/test_agent.py::test_name   # a single test
```

## Conventions

- **Commits / PR titles** use Angular conventional-commits with an optional leading gitmoji:
  `<gitmoji> <type>(<scope>): <subject>`. Types: feat, fix, docs, build, chore, ci, perf, refactor,
  revert, style, test. PRs are squash-merged, so the **PR title** is what must follow the convention.
- Optional features are gated by extras and env vars: `kotaemon[adv]` / `[docling]` / `[paddleocr]`
  / `[lightrag]`, and flags like `USE_NANO_GRAPHRAG`, `USE_LIGHTRAG`, `USE_MULTIMODAL`.
