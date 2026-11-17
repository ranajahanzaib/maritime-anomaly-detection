from fastapi import APIRouter

from backend.app.api.endpoints import (
    overview,
    datasets,
    vessels,
    map,
    events,
    models,
    evaluation,
    jobs,
    export,
)

api_router = APIRouter()

api_router.include_router(overview.router, prefix="/overview", tags=["Overview"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["Datasets"])
api_router.include_router(vessels.router, prefix="/vessels", tags=["Vessels"])
api_router.include_router(map.router, prefix="/map", tags=["Map"])
api_router.include_router(events.router, prefix="/events", tags=["Events"])
api_router.include_router(models.router, prefix="/models", tags=["Models"])
api_router.include_router(evaluation.router, prefix="/evaluation", tags=["Evaluation"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(export.router, prefix="/export", tags=["Export"])
