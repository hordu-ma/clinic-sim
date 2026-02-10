# Repository Guidelines

## Project Structure & Module Organization
- `src/apps/api/`: FastAPI backend (`routes/`, `schemas/`, `models/`, `services/`, `migrations/`).
- `src/apps/web/`: Vue 3 + Vite frontend (`src/views`, `src/api`, `src/stores`, `src/router`).
- `src/infra/compose/`: Docker Compose files for dev and prod (`dev.yml`, `prod-a.yml`, `prod-b.yml`).
- `src/cases/`: seed case JSON files.
- `tests/`: backend pytest suite (integration and service/config tests).
- `src/scripts/`: utility scripts (for example `start_vllm_dev.sh`, `import_cases.py`).

## Build, Test, and Development Commands
- Backend deps: `uv sync --extra dev`
- Frontend deps: `cd src/apps/web && npm install`
- Start local stack (API + PostgreSQL + MinIO): `docker compose -f src/infra/compose/dev.yml up -d`
- Start frontend dev server: `cd src/apps/web && npm run dev`
- Run backend tests: `pytest`
- Run coverage: `pytest --cov=src/apps/api --cov-report=term-missing`
- Lint backend: `ruff check .`
- Type-check backend: `mypy src`
- Build frontend: `cd src/apps/web && npm run build`

## Coding Style & Naming Conventions
- Python: 4-space indentation, type hints for new/changed code, max line length `100` (Ruff).
- Python modules/functions: `snake_case`; classes/Pydantic models: `PascalCase`; constants: `UPPER_SNAKE_CASE`.
- Vue/TypeScript: keep view components in `src/views` with `PascalCase.vue` names (for example `SessionList.vue`); API wrappers in `src/api/*.ts`.
- Keep route/schema/model names aligned across backend layers (`routes/sessions.py` ↔ `schemas/sessions.py` ↔ `models/sessions.py`).

## Testing Guidelines
- Framework: `pytest` with `pytest-asyncio` (`asyncio_mode=auto`).
- Naming: files `test_*.py`, classes `Test*`, functions `test_*` (enforced in `pyproject.toml`).
- Prefer integration-style tests for API flow (`tests/test_integration.py`) and focused unit tests for services (`tests/test_scoring.py`).
- Mock external LLM calls in tests; do not hit real model endpoints in CI.

## Commit & Pull Request Guidelines
- Follow Conventional Commit style seen in history: `feat: ...`, `fix: ...`, `refactor(scope): ...`, `docs: ...`.
- Keep commits scoped and atomic (separate API, web, and infra changes when possible).
- PRs should include a clear summary, linked issue/task (if available), and test evidence (`pytest`, frontend build output).
- Add screenshots or GIFs for UI updates.
- Add migration notes when touching `src/apps/api/migrations/`.

## Security & Configuration Tips
- Copy `.env.example` to `.env`; never commit real secrets.
- Required sensitive vars include `JWT_SECRET`, DB/MinIO passwords, and `LLM_BASE_URL`.
- In production, disable Swagger and avoid default dev credentials.
