from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from app.api.schemas.project import ProjectResponse, ProjectListResponse, SceneSchema
from app.api.schemas.upload import VideoMetadataSchema, VideoDimensionsSchema
from app.api.schemas.processing import ProcessingStartResponse, ProcessingStatusResponse, ProcessingProgressResponse
from app.dependencies.services import get_project_service, get_ai_pipeline_service
from app.services.project import ProjectService
from app.services.ai_pipeline import AIPipelineService
from app.domain.models.analysis import ProcessingContext
from app.domain.models.pipeline import PipelineStatus
from app.domain.models.video import VideoStatus
from app.core.exceptions import NotFoundException
from app.domain.models.video import Video

router = APIRouter()

def _map_video_to_project_response(video: Video) -> ProjectResponse:
    metadata_schema = None
    if video.metadata:
        metadata_schema = VideoMetadataSchema(
            size_bytes=video.metadata.size_bytes,
            duration_seconds=video.metadata.duration_seconds,
            fps=video.metadata.fps,
            codec=video.metadata.codec,
            resolution=video.metadata.resolution,
            dimensions=VideoDimensionsSchema(
                width=video.metadata.dimensions.width,
                height=video.metadata.dimensions.height
            ),
            format=video.metadata.format
        )
        
    scenes_schema = [
        SceneSchema(
            scene_id=s.scene_id,
            seconds_start=s.seconds_start,
            seconds_end=s.seconds_end,
            title=s.title,
            summary=s.summary,
            transcript=s.transcript,
            tags=s.tags
        ) for s in video.scenes
    ]
    
    return ProjectResponse(
        id=video.id,
        project_name=video.project_name,
        status=video.state.status,
        metadata=metadata_schema,
        created_at=video.created_at,
        updated_at=video.updated_at,
        scenes=scenes_schema
    )

@router.get(
    "/",
    response_model=ProjectListResponse,
    summary="List all projects",
    description="Retrieves a paginated list of all video projects."
)
async def list_projects(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    sort_by: Optional[str] = Query(None, description="Field to sort by (e.g. created_at, project_name)"),
    status: Optional[VideoStatus] = Query(None, description="Filter by project status"),
    project_service: ProjectService = Depends(get_project_service)
) -> ProjectListResponse:
    videos, total = await project_service.get_all_projects(limit=limit, offset=offset, sort_by=sort_by, status=status)
    data = [_map_video_to_project_response(v) for v in videos]
    return ProjectListResponse(data=data, total=total)

@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project by ID",
    description="Retrieves a specific project by its ID."
)
async def get_project(
    project_id: str = Path(...),
    project_service: ProjectService = Depends(get_project_service)
) -> ProjectResponse:
    try:
        video = await project_service.get_project_by_id(project_id)
        return _map_video_to_project_response(video)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project",
    description="Deletes a project and all its associated data."
)
async def delete_project(
    project_id: str = Path(...),
    project_service: ProjectService = Depends(get_project_service)
) -> None:
    try:
        await project_service.delete_project(project_id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post(
    "/{project_id}/duplicate",
    response_model=ProjectResponse,
    summary="Duplicate project",
    description="Duplicates a project and all its associated business data."
)
async def duplicate_project(
    project_id: str = Path(...),
    project_service: ProjectService = Depends(get_project_service)
) -> ProjectResponse:
    try:
        new_video = await project_service.duplicate_project(project_id)
        return _map_video_to_project_response(new_video)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post(
    "/{project_id}/process",
    response_model=ProcessingStartResponse,
    summary="Start processing",
    description="Synchronously starts AI processing for the project."
)
async def process_project(
    project_id: str = Path(...),
    force: bool = Query(False, description="Restart processing even if the project is marked Processing/Completed."),
    project_service: ProjectService = Depends(get_project_service),
    pipeline_service: AIPipelineService = Depends(get_ai_pipeline_service)
) -> ProcessingStartResponse:
    try:
        video = await project_service.get_project_by_id(project_id)

        if not force and video.state.status in [VideoStatus.PROCESSING, VideoStatus.COMPLETED]:
            # A crash mid-pipeline leaves the status stuck at Processing with no
            # completion timestamp — treat such stale runs as restartable.
            stale = (
                video.state.status == VideoStatus.PROCESSING
                and video.state.started_at is not None
                and (datetime.now(timezone.utc) - video.state.started_at).total_seconds() > 600
            )
            if not stale:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Project is currently {video.state.status.value}"
                )

        context = ProcessingContext(video=video, current_stage_name="Initialization")
        result = await pipeline_service.process(context)

        # Map pipeline outcome onto the video lifecycle status
        final_status = (
            VideoStatus.COMPLETED
            if result.status in (PipelineStatus.SUCCESS, PipelineStatus.PARTIAL_SUCCESS)
            else VideoStatus.FAILED
        )
        return ProcessingStartResponse(
            project_id=project_id,
            status=final_status,
            message="Processing completed synchronously." if final_status == VideoStatus.COMPLETED
            else f"Processing failed: {result.error_message or 'all scenes failed.'}"
        )
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get(
    "/{project_id}/status",
    response_model=ProcessingStatusResponse,
    summary="Get processing status",
    description="Retrieves the current status of project processing."
)
async def get_project_status(
    project_id: str = Path(...),
    project_service: ProjectService = Depends(get_project_service)
) -> ProcessingStatusResponse:
    try:
        video = await project_service.get_project_by_id(project_id)
        return ProcessingStatusResponse(
            status=video.state.status,
            started_at=video.state.started_at,
            completed_at=video.state.completed_at,
            error_message=video.state.error_message
        )
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get(
    "/{project_id}/progress",
    response_model=ProcessingProgressResponse,
    summary="Get processing progress",
    description="Retrieves the current progress of project processing."
)
async def get_project_progress(
    project_id: str = Path(...),
    project_service: ProjectService = Depends(get_project_service)
) -> ProcessingProgressResponse:
    try:
        video = await project_service.get_project_by_id(project_id)
        return ProcessingProgressResponse(
            progress_percent=video.state.progress_percent,
            current_stage=video.state.current_stage
        )
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

from app.api.schemas.results import SceneListResponse, CaptionListResponse, CaptionResponse, ProjectSummaryResponse

@router.get(
    "/{project_id}/scenes",
    response_model=SceneListResponse,
    summary="Get project scenes",
    description="Retrieves all scenes for a specific project."
)
async def get_project_scenes(
    project_id: str = Path(...),
    project_service: ProjectService = Depends(get_project_service)
) -> SceneListResponse:
    try:
        video = await project_service.get_project_by_id(project_id)
        project_resp = _map_video_to_project_response(video)
        return SceneListResponse(
            data=project_resp.scenes,
            total=len(project_resp.scenes)
        )
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get(
    "/{project_id}/captions",
    response_model=CaptionListResponse,
    summary="Get project captions",
    description="Retrieves all captions for all scenes in a specific project."
)
async def get_project_captions(
    project_id: str = Path(...),
    project_service: ProjectService = Depends(get_project_service)
) -> CaptionListResponse:
    try:
        video = await project_service.get_project_by_id(project_id)
        
        captions_data = []
        for scene in video.scenes:
            if scene.captions:
                captions_data.append(
                    CaptionResponse(
                        scene_id=scene.scene_id,
                        seconds_start=scene.seconds_start,
                        seconds_end=scene.seconds_end,
                        captions=scene.captions
                    )
                )
                
        return CaptionListResponse(
            data=captions_data,
            total=sum(len(c.captions) for c in captions_data)
        )
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get(
    "/{project_id}/summary",
    response_model=ProjectSummaryResponse,
    summary="Get project summary",
    description="Retrieves aggregated statistics for a specific project."
)
async def get_project_summary(
    project_id: str = Path(...),
    project_service: ProjectService = Depends(get_project_service)
) -> ProjectSummaryResponse:
    try:
        summary_data = await project_service.get_project_summary(project_id)
        return ProjectSummaryResponse(**summary_data)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
