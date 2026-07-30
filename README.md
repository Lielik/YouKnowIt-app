# YouKnowIt — App

Flashcard study application built with FastAPI and PostgreSQL. Part of a three-repository DevOps portfolio demonstrating end-to-end software delivery from local development to production on AWS EKS.

**Repositories:** [YouKnowIt-app](https://github.com/Lielik/YouKnowIt-app) · [YouKnowIt-infra](https://github.com/Lielik/YouKnowIt-infra) · [YouKnowIt-gitops](https://github.com/Lielik/YouKnowIt-gitops)

---

## What it does

Users create decks of flashcards and study them in timed review sessions. The app tracks per-card progress and exposes overall statistics. Authentication is cookie-based with HTTP-only JWTs signed with a secret key stored in AWS Secrets Manager and injected at runtime via External Secrets Operator.

---

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI 0.136, Python 3.12 |
| Database | PostgreSQL 16 (SQLAlchemy 2.0, psycopg2) |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Templates | Jinja2, TailwindCSS |
| Metrics | prometheus-fastapi-instrumentator |
| Tests | pytest, pytest-asyncio |
| Container | Docker (multi-stage build) |
| Local dev | Docker Compose |

---

## Project structure

```
app/
├── core/
│   ├── config.py          # Pydantic settings — reads env vars at startup
│   ├── security.py        # bcrypt hashing, JWT encode/decode
│   └── dependencies.py    # FastAPI dependency injection (get_current_user)
├── models/                # SQLAlchemy ORM models
│   ├── user.py
│   ├── deck.py
│   ├── card.py
│   ├── session.py
│   └── progress.py
├── routers/               # Route handlers
│   ├── auth.py            # Login, logout, register
│   ├── decks.py
│   ├── cards.py
│   ├── sessions.py        # Study session lifecycle
│   └── stats.py
├── schemas/               # Pydantic request/response models
├── templates/             # Jinja2 HTML templates
│   ├── auth/login.html
│   ├── shelf/             # Deck library
│   ├── review/            # Active study session
│   └── stats/
├── static/                # CSS and JS
├── database.py            # SQLAlchemy engine + session factory
└── main.py                # App entry point, router registration, /metrics
tests/
├── unit/                  # Schema validation, security functions
└── integration/           # Full API tests against a live PostgreSQL instance
```

---

## Local development

**Prerequisites:** Docker and Docker Compose.

```bash
# Copy the example env file and fill in values
cp .env.example .env

# Start the app and database
docker compose up
```

The app is available at `http://localhost:8000`. Code changes reload automatically — Docker Compose mounts `./app` into the container.

**Environment variables (`.env`):**

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing key — use `openssl rand -hex 32` |
| `DEBUG` | Set `true` to enable `/docs` and `/redoc` |

---

## Running tests

```bash
# Install dependencies
pip install -r requirements.txt

# Unit tests (no database required)
pytest tests/unit/ -v

# Integration tests (requires PostgreSQL)
DATABASE_URL=postgresql://user:pass@localhost:5432/youknowit \
SECRET_KEY=any-value-for-tests \
pytest tests/integration/ -v
```

---

## API endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Create account |
| `POST` | `/api/auth/login` | Login, sets HTTP-only cookie |
| `POST` | `/api/auth/logout` | Clear session cookie |
| `GET/POST` | `/api/decks` | List and create decks |
| `GET/PUT/DELETE` | `/api/decks/{id}` | Manage a single deck |
| `GET/POST` | `/api/decks/{id}/cards` | List and create cards |
| `GET/PUT/DELETE` | `/api/cards/{id}` | Manage a single card |
| `POST` | `/api/sessions` | Start a study session |
| `PUT` | `/api/sessions/{id}` | Answer a card, advance session |
| `GET` | `/api/stats` | Overall study statistics |
| `GET` | `/health` | Liveness probe |
| `GET` | `/metrics` | Prometheus metrics |

Page routes (`/`, `/shelf`, `/shelf/{id}`, `/review`, `/stats`) serve server-rendered HTML.

---

## CI/CD pipeline

The pipeline is defined in `.github/workflows/ci-cd.yml` and runs on every push to `main` and `feature/*`, and on pull requests to `main`.

```
test-unit → build-image → test-integration → release → notify
```

| Job | Runs on | Description |
|---|---|---|
| `test-unit` | all branches | pytest unit tests, no database |
| `build-image` | all branches | `docker build`, caches image by commit SHA |
| `test-integration` | all branches | pytest integration tests against PostgreSQL service container |
| `release` | `main` and `feature/*` only | Pushes image to ECR, tags repo, updates GitOps |
| `notify` | always | Slack Block Kit notification with per-job status |

**Versioning:**
- `main` branches increment a semver patch tag (`v0.0.1`, `v0.0.2`, …) and push `latest` to ECR.
- `feature/*` branches get a `feature-<branch>-<sha>` tag without touching semver.

**GitOps update:** After a successful `main` push, the pipeline clones `YouKnowIt-gitops` using a GitHub PAT (`GITOPS_PAT`), updates `charts/youknowit/values.yaml` with the new image tag, and pushes the commit. ArgoCD polls for the change and deploys it to the cluster within its next sync cycle.

**AWS authentication:** The pipeline uses OIDC — no long-lived AWS keys are stored. The `release` job requests a short-lived token from GitHub's identity provider and assumes an IAM role configured to trust this repository.

**Required GitHub secrets and variables:**

| Name | Type | Description |
|---|---|---|
| `AWS_REGION` | Variable | e.g. `us-east-1` |
| `ECR_REPOSITORY` | Variable | Full ECR repository URI |
| `AWS_ROLE_ARN` | Variable | IAM role ARN for OIDC |
| `SECRET_KEY` | Secret | JWT signing key (for test jobs) |
| `POSTGRES_USER` | Secret | Integration test DB user |
| `POSTGRES_PASSWORD` | Secret | Integration test DB password |
| `POSTGRES_DB` | Secret | Integration test DB name |
| `GITOPS_PAT` | Secret | GitHub PAT with `repo` scope for GitOps repo |
| `SLACK_WEBHOOK_URL` | Secret | Slack incoming webhook URL |

---

## Docker

The Dockerfile uses a two-stage build to keep the final image lean:

1. **Builder stage** — installs all Python dependencies into `/app/packages`.
2. **Final stage** — copies only the installed packages and application code. No build tools, no pip, no cache.

The app runs as a non-root user (`appuser`). The `PYTHONPATH` environment variable points to `/app/packages` so Python can find installed dependencies without a virtual environment.

---

## Security notes

- Passwords are hashed with bcrypt via passlib.
- JWTs are stored in HTTP-only cookies — not accessible to JavaScript.
- `SECRET_KEY` and `DATABASE_URL` are never committed. In production they are injected from AWS Secrets Manager via External Secrets Operator.
- The API docs (`/docs`, `/redoc`) are disabled when `DEBUG=false`.
- The container runs as a non-root user.
