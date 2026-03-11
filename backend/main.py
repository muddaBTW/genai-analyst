"""
GenAI Data Analyst — FastAPI Backend
Main application entry point. Sets up CORS, mounts routers, and manages shared state.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import traceback

# Load environment variables from .env (override system env vars)
load_dotenv(override=True)

# Import routers
from routers import upload, analysis, visualizations, insights, query, report

app = FastAPI(
    title="GenAI Data Analyst API",
    description="AI-powered data analysis backend",
    version="1.0.0",
)

# ── CORS — allow the React dev server ──────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers ──────────────────────────────────────────────────────────
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
app.include_router(visualizations.router, prefix="/api", tags=["Visualizations"])
app.include_router(insights.router, prefix="/api", tags=["AI Insights"])
app.include_router(query.router, prefix="/api", tags=["Query"])
app.include_router(report.router, prefix="/api", tags=["Report"])


# ── Global exception handler — ensures CORS headers on ALL errors ──────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions so the response always includes CORS headers."""
    traceback.print_exc()  # Log the full traceback to the console
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


@app.get("/")
def root():
    return {"message": "GenAI Data Analyst API is running"}
