# Deploy Checklist

## Required env vars

- `POSTGRES_PASSWORD`
- `MINIO_ROOT_PASSWORD`
- `JWT_SECRET`
- `LLM_BASE_URL`
- `LLM_MODEL`

## Deploy sequence

1. Core services up on B server.
2. API up and healthy.
3. Frontend build artifacts ready.
4. Nginx up on A server with certs.
5. End-to-end smoke tests.
