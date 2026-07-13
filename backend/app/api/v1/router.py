"""
API v1 Aggregator Router.
Registers all version 1 endpoints centrally.
"""
from fastapi import APIRouter

# Import existing system endpoints
from app.api.v1.endpoints import system

# Import placeholder module routers
from app.api.v1.upload.router import router as upload_router
from app.api.v1.projects.router import router as projects_router
from app.api.v1.processing.router import router as processing_router
from app.api.v1.captions.router import router as captions_router
from app.api.v1.exports.router import router as exports_router
from app.api.v1.users.router import router as users_router
from app.api.v1.admin.router import router as admin_router
from app.api.v1.tasks.router import router as tasks_router
from app.api.v1.auth.router import router as auth_router
from app.api.v1.auth.sessions_router import router as sessions_router

v1_router = APIRouter()

# Register implemented endpoints
v1_router.include_router(system.router, tags=["system"])

# Register future placeholder endpoints
v1_router.include_router(upload_router, prefix="/upload", tags=["upload"])
v1_router.include_router(projects_router, prefix="/projects", tags=["projects"])
v1_router.include_router(processing_router, prefix="/processing", tags=["processing"])
v1_router.include_router(captions_router, prefix="/captions", tags=["captions"])
v1_router.include_router(exports_router, prefix="/exports", tags=["exports"])
v1_router.include_router(users_router, prefix="/users", tags=["users"])
v1_router.include_router(admin_router, prefix="/admin", tags=["admin"])
v1_router.include_router(tasks_router, tags=["tasks"])
v1_router.include_router(auth_router, prefix="/auth", tags=["auth"])
v1_router.include_router(sessions_router, prefix="/auth/sessions", tags=["auth", "sessions"])

