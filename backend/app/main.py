
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import bus, deviation, eta, gps, health

app = FastAPI(title="TrackBus API", version="0.1.0")

# Allow the local development frontend to call the hosted API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5501"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(health.router)
app.include_router(gps.router, prefix="/api/v1")
app.include_router(bus.router, prefix="/api/v1")
app.include_router(eta.router, prefix="/api/v1")
app.include_router(deviation.router, prefix="/api/v1")
