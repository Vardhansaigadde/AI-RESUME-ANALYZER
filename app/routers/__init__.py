"""API routers package.

Contains endpoint definitions for handling resume uploads, parsing requests,
job description matching, and model inference results.
"""

from app.routers.analyze import router as analyze_router

__all__ = ["analyze_router"]
