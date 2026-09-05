import logging
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import config, db
from app.error_log import log_exception
from app.routes import auth_routes, health, library_routes, player_routes, settings_routes

config.ensure_dirs()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(
            config.LOGS_DIR / "app.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8"
        ),
    ],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Audiobook Backup Tool", lifespan=lifespan)

app.include_router(health.router)
app.include_router(auth_routes.router)
app.include_router(library_routes.router)
app.include_router(settings_routes.router)
app.include_router(player_routes.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log_exception(f"route:{request.url.path}", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.mount("/covers", StaticFiles(directory=str(config.COVERS_DIR)), name="covers")
app.mount("/", StaticFiles(directory=str(config.STATIC_DIR), html=True), name="static")
