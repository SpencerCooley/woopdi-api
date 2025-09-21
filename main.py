from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware


import routers
from celery_app import tasks

app = FastAPI(
    title="AI Backend",
    version="0.0.1",
)
app.mount("/static", StaticFiles(directory="static"), name="static")

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(routers.tools.router)
# all auth related endpoints
app.include_router(routers.auth.router)
app.include_router(routers.user.router)
app.include_router(routers.invitation.routes.router)
app.include_router(routers.subscription.router)
app.include_router(routers.system_settings.router)
app.include_router(routers.organization_user.router)
app.include_router(routers.organization.router)
app.include_router(routers.asset.router)
