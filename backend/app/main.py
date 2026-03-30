from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.trip_routes import router as trip_router

app = FastAPI(title="Driving Matrix API")

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trip_router)


@app.get("/")
def root():
    return {"message": "Driving Matrix API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}