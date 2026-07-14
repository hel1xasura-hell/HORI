"""Custom exception hierarchy used throughout the Hori bot.

Centralizing exceptions here keeps error handling consistent and makes it
possible to catch specific failure categories at the appropriate layer.
"""

from __future__ import annotations


class HoriError(Exception):
    """Base class for all Hori-specific exceptions."""


class ConfigurationError(HoriError):
    """Raised when the bot configuration is invalid or incomplete."""


class DatabaseConnectionError(HoriError):
    """Raised when the bot fails to connect to, or communicate with, MongoDB."""


class RepositoryError(HoriError):
    """Raised when a database repository operation fails unexpectedly."""


class PermissionDeniedError(HoriError):
    """Raised when a user attempts an action they are not authorized to perform."""


class InvalidArgumentError(HoriError):
    """Raised when a command receives arguments that cannot be parsed or are invalid."""


class TargetUserNotFoundError(HoriError):
    """Raised when a command's target user cannot be resolved."""


class ChatSettingsError(HoriError):
    """Raised when reading or writing per-chat settings fails."""


class SchedulerError(HoriError):
    """Raised when the job scheduler fails to start, stop, or schedule a job."""


class ModuleRegistrationError(HoriError):
    """Raised when a feature module fails to register its handlers."""
