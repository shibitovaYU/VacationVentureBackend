from fastapi import FastAPI

from app.api.routes import router
from app.core.firebase import init_firebase


init_firebase()

app = FastAPI(title="Reco Events Collector")
app.include_router(router)
