from contextlib import asynccontextmanager
from fastapi import FastAPI

from exercise_3.infrastructure.api.routers import alerts
from exercise_3.dependencies import audit_repository


# Define the lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the SQLite schema before the app starts accepting requests
    await audit_repository.initialize_schema()
    yield


app = FastAPI(
    title="Security Alerts API",
    description="A REST API to manage and query security alerts with real-time in-memory duplicate detection.",
    version="3.0.0",
    lifespan=lifespan,
)

app.include_router(alerts.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
