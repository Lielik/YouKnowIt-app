# Entry point of the application
# Wires together all routers, middleware, and startup logic

from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user, get_optional_user
from app.database import Base, engine, get_db
from app.models.user import User
from app.routers import auth, decks, cards, sessions, stats

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    # Hide API docs in production
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Serve static files (CSS, JS) from the /static directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

# Register all API routers
app.include_router(auth.router)
app.include_router(decks.router)
app.include_router(cards.router)
app.include_router(sessions.router)
app.include_router(stats.router)

# Expose /metrics endpoint for Prometheus to scrape
Instrumentator().instrument(app).expose(app)


@app.on_event("startup")
def startup():
    # Create all tables on startup — in production Alembic handles this
    Base.metadata.create_all(bind=engine)


# --- Health check ---

@app.get("/health")
def health_check():
    # Used by Docker and Kubernetes to check if the app is running
    return {"status": "healthy"}


# --- Page routes ---
# These routes serve HTML pages to the browser

@app.get("/", response_class=HTMLResponse)
def login_page(request: Request, current_user: User = Depends(get_optional_user)):
    # Redirect to shelf if already logged in
    if current_user:
        return RedirectResponse(url="/shelf")
    return templates.TemplateResponse("auth/login.html", {
        "request": request,
        "current_user": None,
    })


@app.get("/shelf", response_class=HTMLResponse)
def shelf_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.routers.decks import build_deck_response
    from app.models.deck import Deck as DeckModel
    decks_data = db.query(DeckModel).filter(
        DeckModel.user_id == current_user.id).all()
    decks = [build_deck_response(d, current_user.id, db) for d in decks_data]
    return templates.TemplateResponse("shelf/index.html", {
        "request": request,
        "current_user": current_user,
        "active_page": "shelf",
        "decks": decks,
    })


@app.get("/shelf/{deck_id}", response_class=HTMLResponse)
def deck_page(
    deck_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.routers.decks import build_deck_response
    from app.routers.cards import build_card_response
    from app.models.deck import Deck as DeckModel
    from app.models.card import Card as CardModel

    deck = db.query(DeckModel).filter(
        DeckModel.id == deck_id,
        DeckModel.user_id == current_user.id,
    ).first()

    if not deck:
        return RedirectResponse(url="/shelf")

    deck_data = build_deck_response(deck, current_user.id, db)
    cards_data = db.query(CardModel).filter(CardModel.deck_id == deck_id).all()
    cards = [build_card_response(c, current_user.id, db) for c in cards_data]

    return templates.TemplateResponse("shelf/deck.html", {
        "request": request,
        "current_user": current_user,
        "active_page": "shelf",
        "deck": deck_data,
        "cards": cards,
    })


@app.get("/review", response_class=HTMLResponse)
def review_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.routers.decks import build_deck_response
    from app.routers.sessions import build_session_response
    from app.models.deck import Deck as DeckModel
    from app.models.session import StudySession, SessionStatus

    decks_data = db.query(DeckModel).filter(
        DeckModel.user_id == current_user.id).all()
    decks = [build_deck_response(d, current_user.id, db) for d in decks_data]

    paused = db.query(StudySession).filter(
        StudySession.user_id == current_user.id,
        StudySession.status == SessionStatus.PAUSED,
    ).all()
    paused_sessions = [build_session_response(s, db) for s in paused]

    return templates.TemplateResponse("review/index.html", {
        "request": request,
        "current_user": current_user,
        "active_page": "review",
        "decks": decks,
        "paused_sessions": paused_sessions,
    })


@app.get("/stats", response_class=HTMLResponse)
def stats_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.routers.stats import get_overall_stats
    stats_data = get_overall_stats(current_user=current_user, db=db)
    stats_dict = stats_data.model_dump()
    return templates.TemplateResponse("stats/index.html", {
        "request": request,
        "current_user": current_user,
        "active_page": "stats",
        "stats": stats_data,
        "stats_json": stats_dict,
    })
