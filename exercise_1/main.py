from fastapi import FastAPI

from .routers import alerts

app = FastAPI(
    title="Security Alerts API",
    description="A REST API to manage and query security alerts with real-time in-memory duplicate detection.",
    version="1.0.0",
)

app.include_router(alerts.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
