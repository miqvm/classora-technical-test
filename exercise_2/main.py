from fastapi import FastAPI

from exercise_2.infrastructure.api.routers import alerts

app = FastAPI(
    title="Security Alerts API",
    description="A REST API to manage and query security alerts with real-time in-memory duplicate detection.",
    version="2.0.0",
)

app.include_router(alerts.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
