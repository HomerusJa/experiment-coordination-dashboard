"""Defines the logging behavior for the server."""

import logging
import sys

# Custom log levels
TRACE_LEVEL = 5
SUCCESS_LEVEL = 25


class CustomLogger(logging.Logger):
    """Custom logger class to add custom log levels."""

    def trace(self, msg, *args, **kwargs):
        """Issue a TRACE log message."""
        if self.isEnabledFor(TRACE_LEVEL):
            self._log(TRACE_LEVEL, msg, args, **kwargs)

    def success(self, msg, *args, **kwargs):
        """Issue a SUCCESS log message."""
        if self.isEnabledFor(SUCCESS_LEVEL):
            self._log(SUCCESS_LEVEL, msg, args, **kwargs)


# Setup
logging.addLevelName(TRACE_LEVEL, "TRACE")
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")
logging.setLoggerClass(CustomLogger)


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific subsystem.

    Childs for that logger can be created using `logger.getChild("child_name")`.

    This system allows for a consistent logging behavior across the server. It adds the TRACE and SUCCESS log levels.

    Args:
        name (str): The name of the subsystem to log for. (e.g. "s3i")

    Returns:
        logging.Logger: The configured logger for the subsystem.
    """
    __logger = logging.getLogger(name)
    __logger.setLevel(TRACE_LEVEL)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    handler.setFormatter(formatter)
    __logger.addHandler(handler)
    return __logger
