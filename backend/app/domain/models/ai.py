"""
AI Domain Models.
Value objects representing provider-agnostic requests and responses.
Supports fully extensible multimodal inputs (Text, Image, Audio, Video).
"""
from typing import List, Optional, Union, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class AIMessageRole(str, Enum):
    """Standardized roles for conversational message arrays."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class AIContentType(str, Enum):
    """Types of multimodal content."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


@dataclass(kw_only=True)
class AIContentBlock:
    """Base class for all multimodal content blocks.

    Declared ``kw_only`` so subclasses can add required fields alongside the
    discriminator ``type`` (which carries a per-subclass default) without
    tripping the dataclass "non-default argument follows default argument"
    rule. All content blocks are constructed with keyword arguments.
    """
    type: AIContentType


@dataclass(kw_only=True)
class AITextContent(AIContentBlock):
    """Standard text payload."""
    text: str
    type: AIContentType = AIContentType.TEXT


@dataclass(kw_only=True)
class AIImageContent(AIContentBlock):
    """Provider-agnostic image container for Vision Language Models."""
    data_uri: str
    type: AIContentType = AIContentType.IMAGE


@dataclass(kw_only=True)
class AIAudioContent(AIContentBlock):
    """Future placeholder for Audio Language Models."""
    data_uri: str
    type: AIContentType = AIContentType.AUDIO


@dataclass(kw_only=True)
class AIVideoContent(AIContentBlock):
    """Future placeholder for direct Video Language Models."""
    data_uri: str
    type: AIContentType = AIContentType.VIDEO


@dataclass
class AIMessage:
    """A single turn in an AI conversation, supporting interleaved multimodal blocks."""
    role: AIMessageRole
    content: List[Union[AITextContent, AIImageContent, AIAudioContent, AIVideoContent]]


@dataclass
class AIUsage:
    """Provider-agnostic token usage statistics."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class AIModelInfo:
    """Metadata regarding which model ultimately served the request."""
    provider_name: str
    model_name: str


@dataclass
class AIRequest:
    """
    Standardized request ensuring business logic never couples to a specific SDK's payload.
    Supports structured output via json_schema.
    """
    messages: List[AIMessage]
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    response_format: Optional[Dict[str, Any]] = None  # Generic container for JSON Schema enforcement


@dataclass
class AIResponse:
    """Standardized response shielding the application from raw HTTP or SDK responses."""
    content: str
    model_info: AIModelInfo
    usage: AIUsage = field(default_factory=AIUsage)
