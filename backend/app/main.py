"""FastAPI application composition for VoxEthos."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.health import router as health_router
from app.api.routes.research import router as research_router
from app.core.config import settings
from app.core.errors import AppError

app = FastAPI(
    title=f"{settings.platform_name} API",
    summary=settings.tagline,
    version=settings.api_version,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(research_router)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    """Serialize expected application failures into a stable error envelope."""
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.code, "message": exc.message}})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Normalize FastAPI request validation failures for API consumers."""
    return JSONResponse(status_code=422, content={"error": {"code": "VALIDATION_ERROR", "message": "Request validation failed.", "details": exc.errors()}})
