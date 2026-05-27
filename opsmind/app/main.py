
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.db.redis import close_redis
from app.workers.monitoring_manager import monitoring_manager

setup_logging()
logger = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("opsmind_startup", env=settings.APP_ENV)
    await monitoring_manager.startup()
    logger.info("monitoring_manager_ready")

    yield

    logger.info("opsmind_shutdown")
    await monitoring_manager.shutdown()
    await close_redis()
    logger.info("shutdown_complete")


app = FastAPI(
    title="OpsMind API",
    description="AI-powered realtime DevOps incident monitoring",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", error=str(exc), path=request.url.path, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})



app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "name": "OpsMind API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }