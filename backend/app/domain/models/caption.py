"""
Caption Domain Models.
Defines the requests, responses, and entities surrounding caption generation.
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.domain.models.video import CaptionTone
from app.domain.models.ai import AIUsage, AIModelInfo, AIMessage


def _now_utc():
    return datetime.now(timezone.utc)


@dataclass
class CaptionGenerationRequest:
    """
    Standardized request to generate captions for a previously analyzed scene.
    """
    messages: List[AIMessage]
    target_tone: CaptionTone
    temperature: float = 0.7
    max_tokens: int = 500


@dataclass
class CaptionStatistics:
    """Statistics about a generated caption."""
    word_count: int
    character_count: int


@dataclass
class CaptionQuality:
    """Quality metrics for the generated caption."""
    tone_alignment_score: float = 1.0  # Default to 1.0, can be overridden by a judge later
    hallucination_risk: float = 0.0


@dataclass
class CaptionMetadata:
    """Operational metadata regarding the caption generation process."""
    model_info: AIModelInfo
    usage: AIUsage
    generated_at: datetime = field(default_factory=_now_utc)
    provider_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CaptionCandidate:
    """A single generated caption candidate."""
    text: str
    tone: CaptionTone
    statistics: CaptionStatistics
    quality: CaptionQuality = field(default_factory=CaptionQuality)


@dataclass
class CaptionGenerationResult:
    """The result of a caption generation request."""
    candidates: List[CaptionCandidate]
    metadata: CaptionMetadata
