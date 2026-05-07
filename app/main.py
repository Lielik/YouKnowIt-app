# Entry point of the application
# Wires together all routers, middleware, and startup logic

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.database import Base, engine
from app.routers import auth, decks, cards, sessions, stats

# Create all database tables on startup if they don't exist yet
# In production this is handled by Alembic migrations instead
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    # Hide API docs in production
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Serve static files (CSS, JS) from the /static directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Register all routers — each one handles a group of related endpoints
app.include_router(auth.router)
app.include_router(decks.router)
app.include_router(cards.router)
app.include_router(sessions.router)
app.include_router(stats.router)

# Expose /metrics endpoint for Prometheus to scrape
Instrumentator().instrument(app).expose(app)


@app.get("/health")
def health_check():
    # Used by Docker and Kubernetes to check if the app is running
    return {"status": "healthy"}
