v1_router = APIRouter()

# Keep only this
v1_router.include_router(system.router, tags=["system"])

# Temporarily disable everything else
# v1_router.include_router(upload_router, prefix="/upload", tags=["upload"])
# v1_router.include_router(projects_router, prefix="/projects", tags=["projects"])
# v1_router.include_router(processing_router, prefix="/processing", tags=["processing"])
# v1_router.include_router(captions_router, prefix="/captions", tags=["captions"])
# v1_router.include_router(exports_router, prefix="/exports", tags=["exports"])
# v1_router.include_router(users_router, prefix="/users", tags=["users"])
# v1_router.include_router(admin_router, prefix="/admin", tags=["admin"])
# v1_router.include_router(tasks_router, tags=["tasks"])
# v1_router.include_router(auth_router, prefix="/auth", tags=["auth"])
# v1_router.include_router(sessions_router, prefix="/auth/sessions", tags=["auth", "sessions"])
