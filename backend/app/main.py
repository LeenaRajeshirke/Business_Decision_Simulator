import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .database import init_db
from .routers import (
    auth, business, business_data, simulations, insights, compare, reports, notifications,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Decision Simulator API",
    description="Simulate. Understand. Decide.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Never leak stack traces to the client; log server-side instead.
    logger.exception("Unhandled error on %s %s", request.method, request.url)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


@app.on_event("startup")
def on_startup():
    settings.validate()
    init_db()


app.include_router(auth.router)
app.include_router(business.router)
app.include_router(business_data.router)
app.include_router(simulations.router)
app.include_router(insights.router)
app.include_router(compare.router)
app.include_router(reports.router)
app.include_router(notifications.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
