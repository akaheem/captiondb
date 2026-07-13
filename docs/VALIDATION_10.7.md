# CaptionDB — Final Engineering Validation (Phase 10.7)

**Type:** Read-only end-to-end validation & production-readiness audit
**Date:** 2026-07-12
**Scope:** Full-stack (backend `backend/`, frontend `frontend/captiondb-web/`), Docker, contracts in `docs/PROJECT_SPEC.md`
**Mandate:** No feature work, no refactors, no rewrites. Clean Architecture respected. Findings only.

---

## Verdict: ❌ NOT production-ready — 1 BLOCKER breaks backend boot + all backend tests + Docker build

The frontend is in excellent shape. The backend is **architecturally strong** (Clean Architecture, DI, single Fireworks adapter, scrubbed errors, path-traversal defense) but currently **cannot start** due to one import-time dataclass bug, and its **dependency manifest is incomplete**, which also breaks the Docker image. These are small, surgical fixes — but they are hard blockers today.

| Area | Result | Evidence |
|---|---|---|
| Frontend unit tests | ✅ 62/62 pass | `vitest run`, 9 files |
| Frontend typecheck | ✅ pass | `tsc --noEmit` exit 0 |
| Backend import / boot | ❌ **FAILS** | `TypeError` at `app/domain/models/ai.py:32` |
| Backend tests | ❌ **0 collected** | pytest exit 4 (conftest import abort) |
| Dependency manifest | ❌ incomplete | 6 imported pkgs undeclared in `pyproject.toml` |
| Docker build | ❌ **FAILS** | missing `backend/README.md` + undeclared deps |
| Clean Architecture | ✅ strong | layered, DI, interfaces |
| Fireworks single-client | ✅ pass | one adapter behind `AIProvider` |
| Pipeline replaceability | ✅ pass (see note) | constructor DI of stage services |
| Security (errors/upload/paths) | ✅ strong | scrubbed 500s, traversal guard |
| Docker hardening | ✅ strong (once it builds) | multi-stage, non-root, healthcheck, pinned |
| Config-first | ✅ strong | typed pydantic settings groups |
| Logging | ✅ pass | loguru, zero `print()` |

---

## BLOCKERS (must fix before production)

### B1 — Backend cannot import: invalid dataclass field order
**`app/domain/models/ai.py:32-36`** — `AITextContent(AIContentBlock)` inherits `type` (no default) from the base, then declares `text` (no default) *after* it while re-declaring `type` with a default. Python raises at **class-definition / import time**:

```
TypeError: non-default argument 'text' follows default argument 'type'
```

Reproduced in isolation; this is a language-level dataclass rule and fails identically on the declared **Python 3.12** target — not a 3.14-only artifact. The same latent shape exists in the sibling blocks `AIImageContent`, `AIAudioContent`, `AIVideoContent` (lines 39–57): they only avoid the error because their extra field (`data_uri`) has no default *and* precedes the defaulted `type` re-declaration — but the inheritance-plus-redeclaration pattern is fragile throughout.

**Blast radius:** import chain `app.main → app.api.router → app.api.v1.upload.router → app.dependencies → app.domain.interfaces.ai → app.domain.models.ai`. Therefore:
- FastAPI app will not boot.
- `tests/conftest.py:13` imports `app.main.create_app`, so **pytest aborts at collection (exit 4) — 0 of the ~51 test files run.**

**Fix shape (do not implement in this phase):** give the base a defaulted/`field`-ordered `type`, or use `kw_only=True`, or drop the redundant `type` re-declaration on subclasses.

### B2 — Docker image build fails: `COPY ... README.md` target missing
**`backend/Dockerfile:20`** — `COPY pyproject.toml README.md ./`, but **`backend/README.md` does not exist** (`pyproject.toml:10` also declares `readme = "README.md"`). The build fails at this COPY, and even bypassing it, `pip install .` (line 27) invokes hatchling which re-validates the missing readme. Confirmed locally: `pip install -e .` fails with `OSError: Readme file does not exist: README.md`.

### B3 — Incomplete dependency manifest (also a Docker runtime blocker)
**`backend/pyproject.toml:9-17`** declares only 8 runtime deps, but the app imports these **undeclared** packages:

| Package | Imported at (example) |
|---|---|
| `sqlalchemy` (24 sites) | `app/infrastructure/database/engine.py:4` |
| `celery` | `app/infrastructure/tasks/celery_app.py:1` |
| `PyJWT` (`jwt`) | auth infra |
| `asyncpg` | required by `postgresql+asyncpg://` (`app/core/config.py:76`) |
| `greenlet` | SQLAlchemy async runtime |
| `numpy` | pipeline (1 site) |

`requirements.txt` is a stub ("Migrated to pyproject.toml"). Because `Dockerfile:27` runs `pip install .`, the production image would build (once B2 is fixed) with these missing, then **crash at startup with `ModuleNotFoundError`**. `aiosqlite` is also needed if the test suite targets SQLite.

---

## MAJOR / MINOR findings (non-blocking, note for hardening)

- **MINOR — `SecuritySettings.secret_key` default = `"CHANGE_ME_IN_PRODUCTION"`** (`app/core/config.py:34`). Not a committed real secret, but there is no startup guard that refuses to run in production with the placeholder. Recommend a fail-fast check when `APP_ENV=production`.
- **MINOR — DB dev-default password `"postgres"`** (`app/core/config.py:60`). Acceptable as a dev default; ensure it is always overridden via env in deployment (compose uses env — verify no prod path relies on the default).
- **NOTE — `coverage --cov-fail-under=80`** is configured (`pyproject.toml`) but **cannot currently be measured** because the suite does not collect (B1). Coverage claim is unverifiable until B1 is fixed.
- **NOTE — Pipeline stage mapping.** The 11 spec stages are real but split across `app/services/ai_pipeline.py` (orchestrates video-pipeline → vision → caption → scene integration) and `app/services/video_analysis_pipeline.py` (Scene Detection → Frame Sampling → Keyframe → Vision Prep). `app/pipeline/` is an empty package (`__init__.py` only) — orchestration lives under `app/services/`. Stages are injected via constructor DI (replaceable ✓), but the empty `app/pipeline/` package is a naming/expectation mismatch worth a doc note.
- **NOTE — `frontend/README.md`** is the stock AI-Studio/Gemini template (mentions `GEMINI_API_KEY`), not CaptionDB-specific. Documentation-completeness gap only.

---

## Confirmed PASS (independently verified, first-hand)

- **Clean Architecture** — `app/domain/interfaces/*` define abstractions; infrastructure implements them; services take dependencies by constructor injection; composition in `app/dependencies/`. Dependency direction points inward. (Also note: the offending B1 file is a pure domain value-object with only stdlib imports — the layering is clean; the bug is a dataclass declaration error, not an architectural leak.)
- **Fireworks single-client** — the only Fireworks endpoint literal (`https://api.fireworks.ai/...`) is in `app/infrastructure/caption/fireworks_adapter.py:33`, behind the `AIProvider` domain interface (`app/domain/interfaces/ai.py`). No direct Fireworks/httpx calls elsewhere. Provider-swappable ✓. No Fireworks SDK dependency ✓.
- **No hardcoded captions** — caption text is model-generated; tones are enum/config-driven (per prior phase memory + adapter review).
- **Error handling** — `app/api/exception_handlers.py` scrubs all ≥500 responses to `"An internal server error occurred."` (lines 66-70, 108-110); stack traces are logged internally only (`logger.exception`, line 106). No trace/`str(exc)` leakage to clients.
- **Upload / path safety** — streaming chunked upload (OOM mitigation, `upload/router.py:15-21`); storage layer rejects absolute paths and enforces `Path.resolve().relative_to(base)` containment (`app/infrastructure/storage/local.py:44-53`); OS errors wrapped to avoid leaking host paths.
- **Docker hardening** (blocked only by B2/B3): multi-stage builder→production (`Dockerfile:4,32`), pinned `python:3.12-slim`, non-root `USER captiondb` UID/GID 10001 (46-47,62), `HEALTHCHECK` (67), `COPY --chown`. `docker-compose.yml` pins `postgres:15-alpine`, `redis:7-alpine`, healthchecks on all services. No committed `.env`; `.env.example` templates present.
- **Config-first** — `app/core/config.py` uses typed pydantic settings groups (App/API/Logging/Security/CORS/Storage/Database/AIProvider/Processing/BackgroundTask/OAuth). AI `api_key` defaults to `None` (must be supplied).
- **Logging** — loguru-based; **zero `print()`** in `app/` (verified by grep). `asgi-correlation-id` present for request-id propagation.
- **Frontend** — 62/62 vitest tests pass; `tsc --noEmit` clean. (Prior phases confirmed `next build` passes.)

---

## Recommended fix order (for a later implementation phase — NOT this read-only pass)

1. **B1** — correct `AITextContent` field ordering in `app/domain/models/ai.py` (unblocks boot + entire backend test suite).
2. **B3** — add `sqlalchemy`, `celery`, `pyjwt`, `asyncpg`, `greenlet`, `numpy` (and `aiosqlite` for tests) to `pyproject.toml` dependencies.
3. **B2** — add `backend/README.md` (or drop `readme`/the COPY reference).
4. Re-run `pytest` to obtain real pass counts + verify the 80% coverage gate.
5. Address MINOR secret-default guard; align `app/pipeline/` naming; replace the templated `frontend/README.md`.

_After 1–3, the backend should import, the suite should collect, and the Docker image should build — at which point coverage and a live smoke test can be measured (currently impossible)._
