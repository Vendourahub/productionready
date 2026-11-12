"""ProductionReady FastAPI Application Entrypoint."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .api import projects, assessments, remediation, webhooks


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on application boot
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Evidence-backed security verification, remediation, and ASVS 5.0 audit orchestrator.",
    lifespan=lifespan,
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(projects.router)
app.include_router(assessments.router)
app.include_router(remediation.router)
app.include_router(webhooks.router)


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }
