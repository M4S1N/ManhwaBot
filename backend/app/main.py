from app.api.routes import router as root_router
from app.core.config import settings
from app.core.logger import logger
from app.core.middleware import catch_exceptions_middleware
from app.core.rate_limiter import limiter
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, BackgroundTasks

app = FastAPI(title=settings.app_name, debug=settings.debug)

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 App starting...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 App shutting down...")

# Assign rate limiter
app.state.limiter = limiter

# Add CORS middleware
app.add_middleware(CORSMiddleware, **settings.Config.CORS_CONFIG)

# Include API routes
app.include_router(root_router)

# Add exception-catching middleware
app.middleware("http")(catch_exceptions_middleware)