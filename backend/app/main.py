from fastapi import FastAPI

from app.api.routes import bus, deviation, eta, gps, health

app = FastAPI(title="TrackBus API", version="0.1.0")

app.include_router(health.router)
app.include_router(gps.router, prefix="/api/v1")
app.include_router(bus.router, prefix="/api/v1")
app.include_router(eta.router, prefix="/api/v1")
app.include_router(deviation.router, prefix="/api/v1")