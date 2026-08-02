import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.errors import ChronosError, HTTP_STATUS_BY_ERROR
from app.core.observability import log_event, request_context_middleware, request_id_context
from app.services.readiness import readiness_report
from app.api.v1 import auth, commitments, calendar, drift, rescue, reflection, agent, intake, google, scheduling, command, demo, today, plan, settings as settings_api

app = FastAPI(
    title="ChronOS API",
    description="Personal planning and execution service",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(request_context_middleware)

@app.exception_handler(ChronosError)
async def chronos_error_handler(request: Request, exc: ChronosError):
    log_event(logging.getLogger("chronos.error"), logging.WARNING, "handled_error", code=exc.code, path=request.url.path, context=exc.context)
    return JSONResponse(
        status_code=HTTP_STATUS_BY_ERROR[exc.code],
        content={"error": {"code": exc.code, "message": exc.public_message, "request_id": request_id_context.get()}},
    )


@app.get("/api/v1/health/live")
async def liveness():
    return {"status": "alive", "environment": settings.ENV}


@app.get("/api/v1/health/ready")
async def readiness(check_model: bool = False):
    return await readiness_report(check_model=check_model)


@app.get("/api/v1/health")
async def health_compatibility():
    return await readiness_report()

# Include v1 Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(commitments.router, prefix="/api/v1/commitments", tags=["commitments"])
app.include_router(calendar.router, prefix="/api/v1/calendar", tags=["calendar"])
app.include_router(google.router, prefix="/api/v1/google", tags=["google"])
app.include_router(drift.router, prefix="/api/v1/drift", tags=["drift"])
app.include_router(rescue.router, prefix="/api/v1/rescue", tags=["rescue"])
app.include_router(reflection.router, prefix="/api/v1/reflection", tags=["reflection"])
app.include_router(agent.router, prefix="/api/v1/agent", tags=["agent"])
app.include_router(scheduling.router, prefix="/api/v1/scheduling", tags=["scheduling"])
app.include_router(command.router, prefix="/api/v1/command", tags=["command"])
app.include_router(demo.router, prefix="/api/v1/demo", tags=["demo"])
app.include_router(today.router, prefix="/api/v1/today", tags=["today"])
app.include_router(plan.router, prefix="/api/v1/plan", tags=["plan"])
app.include_router(settings_api.router, prefix="/api/v1/settings", tags=["settings"])
from app.api.v1.focus_blocks import router as fb_router
app.include_router(fb_router, prefix="/api/v1/focus-blocks", tags=["focus_blocks"])
app.include_router(intake.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)
