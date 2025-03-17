"""Utility functions for the IBKR event daemon.

This module provides helper functions for loading hook modules and managing file paths.

Example:
    >>> # Load hooks from environment variable
    >>> hooks = prepare_task_path('IBKR_SETUP_PATHS')
    >>> for hook_path in hooks:
    ...     hook = load_hook(hook_path)
    ...     if hook:
    ...         hook.setup(ib, logger)
"""

import glob
import importlib
import os
import sys
from pathlib import Path
from typing import Optional
from typing import Union

from loguru import logger
from typing_extensions import List


def setup_logger(
    log_level: str = "INFO",
    log_file: Optional[Union[str, Path]] = None,
    rotation: str = "100 MB",
    retention: str = "1 week",
    format: str = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",  # noqa: E501
) -> None:
    """Set up loguru logger with specified configuration.

    This function configures the loguru logger with custom formatting and handlers.
    It removes any existing handlers and sets up console and optional file logging.

    Args:
        log_level: The minimum logging level to display. Defaults to "INFO".
        log_file: Optional path to log file. If provided, logs will be written to this file.
        rotation: When to rotate the log file. Defaults to "100 MB".
        retention: How long to keep log files. Defaults to "1 week".
        format: The log message format string. Defaults to a colored format with timestamp,
               level, module, function, line number, and message.

    Example:
        >>> # Basic setup with console logging
        >>> setup_logger()
        >>> # Setup with file logging
        >>> setup_logger(
        ...     log_level="DEBUG",
        ...     log_file="app.log",
        ...     rotation="500 MB",
        ...     retention="2 weeks"
        ... )
        >>> logger.info("Logger configured successfully")
    """
    # Remove any existing handlers
    logger.remove()

    # Add console handler
    logger.add(sys.stderr, format=format, level=log_level, colorize=True)

    # Add file handler if log_file is specified
    if log_file:
        log_file = Path(log_file)
        # Create parent directories if they don't exist
        log_file.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            str(log_file), format=format, level=log_level, rotation=rotation, retention=retention, compression="zip"
        )

    logger.info(f"Logger setup completed. Level: {log_level}, File: {log_file if log_file else 'None'}")


def load_hook(file_path):
    """Load a Python module from a file path as a hook.

    Args:
        file_path: Path to the Python file to load as a hook.

    Returns:
        Optional[module]: The loaded module if successful, None if loading fails.

    Example:
        >>> # Load a hook module
        >>> hook = load_hook('/path/to/my_hook.py')
        >>> if hook:
        ...     # Initialize the hook with IB client
        ...     hook.setup(ib, logger)
        ... else:
        ...     print("Failed to load hook")
    """
    try:
        spec = importlib.util.spec_from_file_location("hook", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logger.error("Failed to load hook from %s: %s", file_path, str(e))
        return None


def collect_pyfile(path: str) -> Optional[list[str]]:
    """Collect Python files from a directory or single file path.

    Args:
        path: Path to a directory or Python file.

    Returns:
        Optional[list[str]]: List of Python file paths if found, None otherwise.

    Example:
        >>> # Collect Python files from a directory
        >>> files = collect_pyfile('/path/to/hooks')
        >>> if files:
        ...     print(f"Found {len(files)} Python files")
        >>> # Check a single file
        >>> result = collect_pyfile('/path/to/single_hook.py')
        >>> if result:
        ...     print("Found Python file:", result[0])
    """
    if os.path.isdir(path):
        pattern = os.path.join(path, "**", "*.py")
        return glob.glob(pattern, recursive=True)
    elif os.path.isfile(path) and path.endswith(".py"):
        return [path]
    return None


def prepare_task_path(file_path: List[str]) -> list[str]:
    """Prepare a list of Python file paths from a list of directory paths.

    This function processes a list of directory paths and collects all Python files
    within those directories, excluding __init__.py files.

    Args:
        file_path: List of directory paths to search for Python files.

    Returns:
        list[str]: List of Python file paths, excluding __init__.py files.

    Example:
        >>> # Process a list of paths
        >>> paths = ['./example', '/another/path']
        >>> files = prepare_task_path(paths)
        >>> print(f"Found {len(files)} Python files")
    """
    env_data = [path for path in file_path if os.path.exists(path)]
    py_files: list[str] = []
    for path in env_data:
        py_files.extend(collect_pyfile(path))
    py_files = [file for file in py_files if not file.endswith("__init__.py")]
    return py_files
