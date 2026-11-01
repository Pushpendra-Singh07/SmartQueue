import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=False)

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from database import Base, engine
from routers import admin_routes, auth_routes, doctor_routes, queue_api, staff_routes

Base.metadata.create_all(bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MEDIFLOW")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "change-this-secret"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/fav", StaticFiles(directory=str(BASE_DIR / "fav")), name="fav")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.include_router(auth_routes.router)
app.include_router(admin_routes.router)
app.include_router(doctor_routes.router)
app.include_router(staff_routes.router)
app.include_router(queue_api.router)


@app.get("/")
def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/health")
def health():
    return {"status": "ok"}
