# Security Checklist

- `.env` and secrets are not committed.
- JWT and service credentials are not hardcoded.
- Production docs endpoints are disabled.
- Database migration behavior is explicit and controlled.
- Rate limiting and auth controls exist on sensitive routes.
