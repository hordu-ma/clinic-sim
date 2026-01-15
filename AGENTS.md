# AGENTS.md

This file guides agentic coding assistants working in this repo.

## Repository Overview

- Backend: FastAPI + SQLAlchemy + Alembic (async).
- Frontend: Vue 3 + TypeScript + Vite + Vant.
- Dependency manager: `uv` for Python, `npm` for web.
- Python version: 3.11 (see `pyproject.toml`).
- Ruff configured (line length 100) and mypy present.

## Build / Lint / Test Commands

### Python backend (repo root)

- Install deps (including dev tools):
  - `uv sync --all-extras`
- Run API locally:
  - `uv run uvicorn src.apps.api.main:app --reload --host 0.0.0.0 --port 8000`
- Lint (Ruff):
  - `uv run ruff check src`
- Format (Ruff formatter):
  - `uv run ruff format src`
- Type check (mypy):
  - `uv run mypy src/apps/api`
- Run tests:
  - `uv run pytest`
- Run a single test file:
  - `uv run pytest tests/test_file.py`
- Run a single test case or function:
  - `uv run pytest tests/test_file.py::TestClass::test_name`
- Run tests matching a name:
  - `uv run pytest -k "keyword"`
- Coverage (pytest-cov is installed):
  - `uv run pytest --cov=src/apps/api --cov-report=term-missing`

### Frontend (src/apps/web)

- Install deps:
  - `npm ci`
- Dev server:
  - `npm run dev`
- Build:
  - `npm run build`
- Preview:
  - `npm run preview`
- Lint/test:
  - No scripts defined in `package.json`. Add `eslint`/`vitest` if needed.

### Infra (optional, if working on compose)

- Start dev stack:
  - `docker compose -f src/infra/compose/dev.yml up -d`

## Code Style Guidelines

### General

- Prefer small, focused changes and keep diffs minimal.
- Respect existing module boundaries: routes → schemas → services → models.
- Keep docstrings for public functions and modules.
- Do not introduce inline comments unless explicitly requested.

### Python Backend

#### Imports & Formatting

- Ruff enforces import sorting (select includes `I`).
- Use import grouping: stdlib, third-party, local, separated by blank lines.
- Follow 100-char line length (`[tool.ruff] line-length = 100`).
- Use f-strings and type hints consistently (e.g., `dict[str, str]`).

#### Types & Naming

- Functions/variables: `snake_case`.
- Classes: `PascalCase`.
- Constants: `UPPER_SNAKE_CASE`.
- Use `type` annotations for function signatures and public data structures.
- Prefer `list[Type]`, `dict[str, Type]`, `str | None` (PEP 604).

#### API Layering (from SKILL.md)

- Route layer: only request validation, dependency injection, and response.
- Service layer: business logic and LLM calls with explicit timeout + logging.
- Schemas: always return Pydantic models; no raw dict responses.
- Do not hardcode secrets; use `Settings` in `src/apps/api/config.py`.

#### Error Handling & Logging

- Use `BusinessError` for domain errors; include `error_code` when possible.
- Use `HTTPException` for request validation/auth failures.
- All uncaught errors funnel through `setup_exception_handlers`.
- Log via `loguru` (`src/apps/api/logging_config.py`).
- Include `trace_id` from request state when logging errors.

#### Database

- Use SQLAlchemy ORM models in `src/apps/api/models`.
- Use async sessions and `select` queries (see `routes/chat.py`).
- Avoid raw SQL unless explicitly required.
- Do not run destructive migrations in production.

#### LLM Usage

- LLM base URL/model are configured via env vars (`LLM_BASE_URL`, `LLM_MODEL`).
- LLM calls must include timeout, error handling, and logging.
- Avoid LLM calls directly in route handlers; place them in services.

### Frontend (Vue 3 + TypeScript)

#### Formatting & Imports

- Use 2-space indentation and semicolons (matches current files).
- Use double quotes in TS/JS (`"`), consistent with existing code.
- Keep imports ordered: Vue, router/pinia, API, types, UI libs.
- Use `type` imports (`import type { Foo } ...`) where appropriate.

#### Naming & Types

- Components: `PascalCase` filenames (`Chat.vue`, `CaseList.vue`).
- Variables/functions: `camelCase`.
- API types live in `src/apps/web/src/types`.
- All API calls live in `src/apps/web/src/api`.
- Do not build API URLs in components; use API helpers.

#### Error Handling & UX

- Use Vant toasts/dialogs for user-visible errors.
- Catch async errors and show user-friendly messages (`showFailToast`).
- Handle auth errors via store + router redirect (see `api/request.ts`).

## Additional Rules

- No Cursor or Copilot rules found in `.cursor/rules/`, `.cursorrules`, or
  `.github/copilot-instructions.md` at time of writing.
- If adding new rules, keep this file up to date.

## Quick References

- Backend entrypoint: `src/apps/api/main.py`
- Settings: `src/apps/api/config.py`
- Error handling: `src/apps/api/exceptions.py`
- Frontend API layer: `src/apps/web/src/api/request.ts`
- Compose files: `src/infra/compose/*.yml`
