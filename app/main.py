import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import config, db
from app.routes import auth_routes, health, library_routes

config.ensure_dirs()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Audiobook Backup Tool", lifespan=lifespan)

app.include_router(health.router)
app.include_router(auth_routes.router)
app.include_router(library_routes.router)

app.mount("/covers", StaticFiles(directory=str(config.COVERS_DIR)), name="covers")
app.mount("/", StaticFiles(directory=str(config.STATIC_DIR), html=True), name="static")
