---
name: production-deploy
description: Deploy clinic-sim production stack across A/B servers with Nginx, API, vLLM, and storage services. Use when preparing production compose configs, environment variables, rollout checks, and post-deploy verification.
---

# Production Deploy

Use this skill for production release and environment checks.

## Execute Workflow

1. Read `references/deploy-checklist.md`.
2. Validate required environment variables before deployment.
3. Deploy entry layer with `src/infra/compose/prod-a.yml`.
4. Deploy core layer with `src/infra/compose/prod-b.yml`.
5. Confirm Nginx SSE proxy behavior and TLS files.
6. Verify API health, auth, chat streaming, and frontend access.

## Guardrails

- Never commit production secrets.
- Keep Swagger disabled in production env.
- Open only required ports.
- Run migration explicitly, not via implicit app startup.

## References

- Deployment checklist: `references/deploy-checklist.md`
- Runtime files map: `references/runtime-files.md`
