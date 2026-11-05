from fastapi import APIRouter

from app.routers.analysis import router as analysis_router
from app.routers.drift import router as drift_router

api_router = APIRouter()
api_router.include_router(analysis_router)
api_router.include_router(drift_router)

