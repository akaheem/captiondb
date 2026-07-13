"""
Vision Analysis Domain Models.

Establishes provider-independent representations for Vision AI payloads and structured results.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from app.domain.models.analysis import VisionInputPackage
from app.domain.models.ai import AIUsage, AIModelInfo, AIMessage

@dataclass
class VisionAnalysisRequest:
    """
    Encapsulates the intent to analyze a specific VisionInputPackage.
    Future-proofs the service layer against signature changes if we need to add request-level
    overrides (e.g., custom prompts, confidence thresholds) per analysis run.
    """
    messages: List[AIMessage]
    response_format: Optional[Dict[str, Any]] = None
    max_tokens: int = 1500
    temperature: float = 0.2


@dataclass
class VisionAnalysisMetadata:
    """
    Captures operational metrics and raw payload context returned by the Vision AI provider.
    Ensures observability without tying the domain to specific SDKs.
    """
    model_info: AIModelInfo
    usage: AIUsage
    confidence_score: Optional[float] = None
    raw_response_metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time_ms: Optional[int] = None


@dataclass
class VisionAnalysisResult:
    """
    A highly structured, semantic extraction of the visual scene context.
    Designed strictly independent of any underlying AI provider JSON schema.
    """
    # Core Semantics
    scene_summary: str
    
    # Detailed Entities
    objects: List[str] = field(default_factory=list)
    people: List[str] = field(default_factory=list)
    activities: List[str] = field(default_factory=list)
    environment: str = ""
    
    # Aesthetics & Tone
    mood: str = ""
    dominant_colors: List[str] = field(default_factory=list)
    
    # Additional Modalities
    ocr_placeholder: str = "" # To be filled directly by Vision AI if instructed, or by a dedicated OCR engine
    
    # Trust & Safety
    safety_flags: List[str] = field(default_factory=list)
    
    # Observability
    metadata: Optional[VisionAnalysisMetadata] = None
