"""
Integration Domain Models.
Defines the result structures for merging AI outputs back into the core Domain.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.domain.models.video import Video, Scene


def _now_utc():
    return datetime.now(timezone.utc)


class IntegrationStatus(str, Enum):
    """Overall status of an integration execution."""
    SUCCESS = "Success"
    PARTIAL_SUCCESS = "Partial_Success"
    FAILED = "Failed"


@dataclass
class CostBreakdown:
    """Estimated cost metrics in arbitrary units (or micro-cents) based on provider usage."""
    estimated_total_cost: float = 0.0
    estimated_vision_cost: float = 0.0
    estimated_caption_cost: float = 0.0


@dataclass
class IntegrationStatistics:
    """Aggregated operational statistics for the integration phase."""
    total_scenes: int = 0
    successful_scenes: int = 0
    failed_scenes: int = 0
    
    # Latencies
    total_vision_latency_seconds: float = 0.0
    total_caption_latency_seconds: float = 0.0
    total_overall_latency_seconds: float = 0.0
    average_scene_latency_seconds: float = 0.0
    
    # Tokens
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0


@dataclass
class SceneIntegrationResult:
    """The result of integrating a single scene."""
    scene_id: str
    is_success: bool
    enriched_scene: Scene
    error_message: Optional[str] = None


@dataclass
class VideoIntegrationResult:
    """
    The final output of integrating the AI Pipeline results into the core Video aggregate.
    """
    video_id: str
    status: IntegrationStatus
    enriched_video: Video
    scene_results: List[SceneIntegrationResult] = field(default_factory=list)
    statistics: IntegrationStatistics = field(default_factory=IntegrationStatistics)
    cost: CostBreakdown = field(default_factory=CostBreakdown)
    error_message: Optional[str] = None
    integrated_at: datetime = field(default_factory=_now_utc)
