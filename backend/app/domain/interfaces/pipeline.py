"""
Abstract Pipeline Interfaces.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class PipelineContext(ABC):
    """
    Abstract state container passed between PipelineStages.
    
    Purpose: To transport data safely across isolated stages without global state.
    Responsibilities: Holding video metadata, scene information, intermediate AI outputs, and final captions.
    Expected Inputs: Key-value updates from pipeline stages.
    Expected Outputs: Stored values when queried by subsequent stages.
    Failure Behavior: Returns None or raises KeyError if a required upstream stage skipped a value.
    Extension Points: Can be backed by an in-memory dictionary, or a database record for resumable pipelines.
    """
    
    @property
    @abstractmethod
    def video_id(self) -> str:
        """The unique identifier for the video being processed."""
        pass

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the pipeline context."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Store a value in the pipeline context."""
        pass


class PipelineStage(ABC):
    """
    Abstract definition of a single isolated step in the video processing workflow.
    
    Purpose: Implements the Chain of Responsibility / Pipeline pattern to keep concerns separated.
    Responsibilities: Execute one specific transformation or side-effect (e.g., ExtractFrames, RunOCR).
    Expected Inputs: The current PipelineContext.
    Expected Outputs: The mutated PipelineContext (or a new instance).
    Failure Behavior: Must raise specific DomainExceptions if the stage fails unrecoverably.
    Extension Points: Can be extended to create arbitrary stages (e.g., SceneDetectionStage, JudgeStage)
                      without modifying the orchestrator.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The unique name of this pipeline stage."""
        pass

    @abstractmethod
    async def execute(self, context: PipelineContext) -> PipelineContext:
        """
        Executes the business logic for this stage.
        Modifies and returns the context.
        """
        pass
