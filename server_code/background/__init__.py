"""Folder containing background tasks."""

from ..logs import get_logger

__all__ = ["bg_logger"]

bg_logger = get_logger("bg")
