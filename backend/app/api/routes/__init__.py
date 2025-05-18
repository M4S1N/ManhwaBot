from .file import router as file_routes
from fastapi import APIRouter

router = APIRouter()
router.include_router(file_routes)
