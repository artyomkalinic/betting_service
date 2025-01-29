from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api import users
from api import admin
from api import pages
from api.config import templates, get_db_connection
from api.gen_matches import add_teams_db, gen_events, set_events

app = FastAPI()

app.include_router(users.router)
app.include_router(admin.router)
app.include_router(pages.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

# uvicorn main:app --reload