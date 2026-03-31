from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db import create_db_and_tables
from app.routers.trip_routes import router as trip_router
from app.routers.resident_routes import router as resident_router
from app.routers.location_routes import router as location_router
from app.routers.driver_routes import router as driver_router
from app.routers.vehicle_routes import router as vehicle_router

app = FastAPI(title=settings.app_name)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

origins = [
    settings.frontend_origin,
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trip_router)
app.include_router(resident_router)
app.include_router(location_router)
app.include_router(driver_router)
app.include_router(vehicle_router)

@app.get("/")
def root():
    return {"message": f"{settings.app_name} is running"}


@app.get("/health")
def health():
    return {"status": "ok"}