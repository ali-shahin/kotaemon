# Repository Guidelines

## Project Structure & Module Organization

Kotaemon is a Python workspace with the app entry points at the repository root (`app.py`, `sso_app.py`, `flowsettings.py`). Core packages live under `libs/`: `libs/kotaemon/kotaemon` contains retrieval, loaders, agents, storage, LLM integrations, and CLI code; `libs/ktem/ktem` contains the application layer. Tests are colocated by package in `libs/kotaemon/tests` and `libs/ktem/ktem_tests`. Documentation and site assets are in `docs/`, templates are in `templates/`, operational scripts are in `scripts/`, and local runtime data is under `ktem_app_data/`.

## Build, Test, and Development Commands

- `uv sync --python 3.11`: create/update the recommended development environment from `uv.lock`.
- `pip install -e "libs/kotaemon[all]" && pip install -e "libs/ktem"`: editable install path when not using `uv`.
- `python app.py`: run the local Kotaemon app after dependencies are installed.
- `bash scripts/run_linux.sh` or `scripts/run_macos.sh`: OS-specific setup/run helpers.
- `pre-commit run --all-files`: run formatting and static checks used by CI.
- `pytest libs/kotaemon/tests/` and `pytest libs/ktem/ktem_tests/`: run package test suites.
- `docker compose up`: run the containerized local stack when Docker is preferred.

## Coding Style & Naming Conventions

Use Python 3.11+ syntax. Follow existing module patterns: snake_case for files, functions, and variables; PascalCase for classes; UPPER_SNAKE_CASE for constants. Keep imports organized with first-party packages `kotaemon` and `ktem`; `isort`, `black`, `flake8`, `codespell`, and pre-commit are configured in project metadata. Prefer small, typed, composable functions and package-local helpers over cross-package shortcuts.

## Testing Guidelines

Tests use `pytest`. Name files `test_*.py` and place them in the owning package test directory. Add focused unit tests for new loaders, stores, agents, prompts, or app services, and include regression tests for bug fixes. `libs/kotaemon/pytest.ini` sets quiet output and writes logs to `logs/pytest-logs.txt`; create or ignore generated logs as appropriate.

## Commit & Pull Request Guidelines

The project uses Angular/Conventional Commit style for PR titles and commits, optionally with gitmoji: `feat: add loader option`, `fix(index): validate paths`, `docs: update setup guide`. PRs should include a clear description, linked issues when relevant, test results, and screenshots or short recordings for UI changes. All GitHub Actions checks, including style, title validation, and unit tests, must pass before merge.

## Git Worktree Workflow

Before implementing a new feature or fixing a bug, create a task-specific branch and a
separate Git worktree. Perform the implementation and validation in that worktree so
multiple tasks can proceed concurrently without interfering with one another. Worktree
names and locations may be chosen per task. Read-only investigation, planning, and trivial
documentation-only changes do not require a separate worktree.

## Task Tracking

Use `.local/tasks.md` for all persistent TODO items and task-status updates. Preserve its
existing sections and content when updating it. The file remains local-only under the
existing `.local/` ignore rule; temporary internal planning does not need to be persisted.

## Security & Configuration Tips

Copy `settings.yaml.example` for local configuration and avoid committing secrets, credentials, model keys, or generated runtime data. Be careful with file path handling, document loaders, and migration scripts; validate user-controlled paths and keep changes scoped to the relevant package.
