"""
Abstract Logging and Configuration Interfaces.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class Logger(ABC):
    """
    Abstract interface for the application logger.
    
    Purpose: Allows domain services to log information without coupling directly to Loguru or standard logging.
    Responsibilities: Emitting log messages at various severities.
    Extension Points: LoguruAdapter, StandardLoggerAdapter.
    """
    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None: pass

    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None: pass

    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None: pass

    @abstractmethod
    def error(self, message: str, **kwargs: Any) -> None: pass


class ConfigurationProvider(ABC):
    """
    Abstract interface for application settings.
    
    Purpose: Decouples domain logic from specific frameworks like Pydantic Settings.
    Responsibilities: Providing strongly typed or raw configuration values.
    """
    @abstractmethod
    def get_value(self, key: str, default: Any = None) -> Any:
        """Retrieve a configuration value by key."""
        pass
