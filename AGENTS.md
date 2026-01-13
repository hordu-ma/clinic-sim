# Repository Guidelines

## Project Structure & Module Organization

- `main.py` is a minimal entry point for quick local runs.
- `src/apps/` is reserved for application code (API/web) and is currently a stub.
- `src/infra/compose/` contains Docker Compose files (`dev.yml`, `prod-a.yml`, `prod-b.yml`).
- `src/cases/` is intended for case data, `src/docs/` for documentation, and `src/scripts/` for helper scripts.

## Build, Test, and Development Commands

- `python main.py` — runs the current minimal CLI stub.
- `docker compose -f src/infra/compose/dev.yml up` — starts the local dev stack (when services are implemented).
- `docker compose -f src/infra/compose/prod-a.yml up` / `prod-b.yml` — production profiles (A: entry/frontend, B: GPU/backend).

## Coding Style & Naming Conventions

- Python code uses 4-space indentation and PEP 8 conventions.
- Names: `snake_case` for variables/functions, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Keep modules small and single-purpose; prefer descriptive filenames over abbreviations.

## Testing Guidelines

- No test framework is configured yet.
- If you add tests, use `pytest`, place tests under `tests/`, and name files `test_*.py`.
- Aim for coverage on core API flows and data validation paths before adding optional features.

## Commit & Pull Request Guidelines

- Recent history uses Conventional Commit style: `feat: ...`, `init ...`.
- Prefer concise, imperative subjects and include scope when helpful (e.g., `feat(api): add chat stream`).
- PRs should include: summary, testing notes/commands, and linked issues. Add screenshots for UI changes.

## Configuration Tips

- Keep environment-specific values in `.env` (not committed). Document required variables in `README.md`.
- When adding services to Compose, mirror dev/prod parity and keep names consistent across files.
