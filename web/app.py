from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from pathlib import Path

from config.settings import settings
from web.routes import auth_routes, dashboard_routes, api_routes

# Create FastAPI app
app = FastAPI(title="TikTok Bot Dashboard", version="1.0.0")

# Middleware
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates and static files
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Include routers
app.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])
app.include_router(dashboard_routes.router, tags=["Dashboard"])
app.include_router(api_routes.router, prefix="/api", tags=["API"])

@app.get("/")
async def root(request: Request):
    """Redirect to dashboard or login."""
    user = request.session.get("user")
    if user:
        return templates.TemplateResponse("home.html", {"request": request, "user": user})
    return templates.TemplateResponse("login.html", {"request": request})