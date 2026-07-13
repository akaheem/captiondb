import contextlib
from typing import AsyncGenerator

from app.core.config import get_settings
from app.dependencies.infrastructure import (
    get_engine,
    get_db_sessionmaker,
    get_unit_of_work,
    get_scene_detector,
    get_frame_extractor,
    get_frame_quality_analyzer,
    get_keyframe_selector,
    get_image_preprocessor,
    get_vision_analyzer,
    get_caption_generator
)
from app.dependencies.services import (
    get_scene_detection_service,
    get_frame_sampling_service,
    get_keyframe_selection_service,
    get_vision_preparation_service,
    get_video_analysis_pipeline,
    get_prompt_builder,
    get_vision_analysis_service,
    get_caption_generation_service,
    get_scene_result_integration_service,
    get_ai_pipeline_service,
    get_storage_provider,
    get_storage_service
)
from app.services.ai_pipeline import AIPipelineService

@contextlib.asynccontextmanager
async def get_ai_pipeline_context() -> AsyncGenerator[AIPipelineService, None]:
    """
    Manually resolves the dependency graph for the AIPipelineService.
    Because Celery workers run outside of the FastAPI request lifecycle,
    we cannot use `Depends()`. We must construct the services manually.
    """
    settings = get_settings()
    engine = get_engine(settings)
    session_maker = get_db_sessionmaker(engine)
    
    # We must yield from the unit of work context if it manages resources,
    # but currently get_unit_of_work just returns the UoW factory wrapper.
    # The UoW context manager is handled inside the Service (async with self._uow).
    uow = get_unit_of_work(session_maker)
    
    storage_provider = get_storage_provider(settings)
    storage_service = get_storage_service(storage_provider)
    
    scene_detector = get_scene_detector()
    scene_service = get_scene_detection_service(scene_detector, storage_service)
    
    frame_extractor = get_frame_extractor()
    frame_service = get_frame_sampling_service(frame_extractor, storage_service)
    
    frame_analyzer = get_frame_quality_analyzer()
    keyframe_selector = get_keyframe_selector(frame_analyzer)
    keyframe_service = get_keyframe_selection_service(keyframe_selector)
    
    try:
        image_preprocessor = get_image_preprocessor()
    except NotImplementedError:
        image_preprocessor = None
    vision_prep_service = get_vision_preparation_service(image_preprocessor)
    
    video_pipeline = get_video_analysis_pipeline(
        scene_service, frame_service, keyframe_service, vision_prep_service
    )
    
    prompt_builder = get_prompt_builder()
    
    try:
        vision_analyzer = get_vision_analyzer()
    except NotImplementedError:
        vision_analyzer = None
    vision_service = get_vision_analysis_service(vision_analyzer, prompt_builder)
    
    try:
        caption_generator = get_caption_generator(settings)
    except NotImplementedError:
        caption_generator = None
    caption_service = get_caption_generation_service(caption_generator, prompt_builder)
    
    scene_integration = get_scene_result_integration_service()
    
    ai_pipeline = get_ai_pipeline_service(
        video_pipeline, vision_service, caption_service, scene_integration, uow
    )
    
    yield ai_pipeline
