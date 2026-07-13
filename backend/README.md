# CaptionDB Backend

AI-powered video captioning backend for [CaptionDB](../README.md).

Transforms uploaded videos into high-quality, multi-style captions using Vision
Language Models via a provider-agnostic AI pipeline. Built with FastAPI following
Clean Architecture (Domain / Application / Infrastructure / API).

## Stack

- Python 3.12+, FastAPI, Pydantic v2
- SQLAlchemy (async) + PostgreSQL (`asyncpg`)
- Celery + Redis for background processing
- Fireworks AI (behind a provider-agnostic `AIProvider` interface)
- Structured logging via Loguru

## Layout

```
app/
  api/             REST API (versioned routers, schemas)
  application/     use-case services
  domain/          entities, value objects, interfaces (no external deps)
  infrastructure/  adapters: storage, database, caption/vision, tasks, auth
  core/            settings (pydantic BaseSettings), config
migrations/        Alembic migrations
tests/             pytest suite
```

## Local development

```bash
# Install (runtime + test extras)
pip install -e ".[test]"

# Run the API
uvicorn app.main:app --reload

# Run the test suite
pytest
```

Configuration is environment-driven — see `.env.example`. No secrets are committed.

## Docker

The service is built as a multi-stage, non-root image:

```bash
docker build -t captiondb/api:latest .
```

Or via the root Compose stack (API + Postgres + Redis + Celery):

```bash
docker compose up --build
```

Health check: `GET /api/v1/health/live`.
