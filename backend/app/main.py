from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import supabase_client
from app.api.v1 import auth, commitments, calendar, drift, rescue, reflection, agent, intake, google, scheduling

app = FastAPI(
    title="ChronOS API",
    description="Proactive AI Time Operating System Backend Service",
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

# Health Check Route
@app.get("/api/v1/health")
async def health_check():
    db_ok = False
    if supabase_client is not None:
        try:
            # Check connection presence by validating configuration variables
            db_ok = bool(settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY)
        except Exception:
            db_ok = False

    return {
        "status": "healthy",
        "environment": settings.ENV,
        "supabase_configured": db_ok,
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "google_oauth_configured": bool(settings.GOOGLE_CLIENT_ID)
    }

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
from app.api.v1.focus_blocks import router as fb_router
app.include_router(fb_router, prefix="/api/v1/focus-blocks", tags=["focus_blocks"])
app.include_router(intake.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)
