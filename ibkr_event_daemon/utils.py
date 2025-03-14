"""Utility functions for IB Event Daemon.

This module provides utility functions for loading hooks and managing task paths.
It includes functionality for:
- Loading hook modules dynamically
- Collecting Python files from directories
- Preparing task paths from environment variables
"""
import glob
import importlib
import os
from logging import getLogger
from typing import Optional


def load_hook(file_path: str) -> Optional[callable]:
    """Load a Python module from a file path.

    This function dynamically loads a Python module from the given file path.
    The module can contain any number of functions or classes that will be
    used as hooks in the IB Event Daemon.

    Args:
        file_path: Absolute path to the Python module file.

    Returns:
        The loaded module object if successful, None if loading fails.

    Example:
        >>> hook = load_hook("/path/to/hook.py")
        >>> if hook and hasattr(hook, 'on_trade'):
        ...     hook.on_trade(trade_event)
    """
    logger = getLogger(__name__)
    try:
        spec = importlib.util.spec_from_file_location("hook", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        logger.info("Successfully loaded hook from %s", file_path)
        return module
    except Exception as e:
        logger.error("Failed to load hook from %s: %s", file_path, str(e))
        return None


def collect_pyfile(path: str) -> Optional[list[str]]:
    """Collect Python files from a path.
    
    This function collects Python files (.py) from a given path. If the path
    is a directory, it will recursively collect all Python files. If the path
    is a file, it will return that file if it's a Python file.
    
    Args:
        path: Path to a file or directory to collect Python files from.
    
    Returns:
        A list of absolute paths to Python files, or None if no Python files
        are found or the path is invalid.
    
    Example:
        >>> files = collect_pyfile("/path/to/hooks")
        >>> if files:
        ...     for file in files:
        ...         print(f"Found Python file: {file}")
    """
    if os.path.isdir(path):
        pattern = os.path.join(path, "**", "*.py")
        return glob.glob(pattern, recursive=True)
    elif os.path.isfile(path) and path.endswith(".py"):
        return [path]
    return None


def prepare_task_path(env_key: str = "IB_DAEMON_HANDLERS") -> list[str]:
    """Prepare task paths from environment variable.
    
    This function reads a list of paths from an environment variable,
    validates them, and collects all Python files from those paths.
    The paths in the environment variable should be separated by
    the system path separator.
    
    Args:
        env_key: Name of the environment variable containing task paths.
            Defaults to "IB_DAEMON_HANDLERS".
    
    Returns:
        A list of absolute paths to Python task files, excluding __init__.py
        files.
    
    Example:
        >>> # Set environment variable
        >>> os.environ["IB_DAEMON_HANDLERS"] = "/path/to/tasks:/another/path"
        >>> task_files = prepare_task_path()
        >>> print(f"Found {len(task_files)} task files")
    """
    logger = getLogger(__name__)
    env_data: list[str] = os.getenv(env_key, "").split(os.pathsep)
    logger.info("Loading tasks from paths: %s", os.pathsep.join(env_data))
    
    # 过滤不存在的路径
    env_data = [path for path in env_data if os.path.exists(path)]
    if len(env_data) == 0:
        logger.warning("No valid task paths found in %s", env_key)
        return []
    
    # 收集 Python 文件
    py_files: list[str] = []
    for path in env_data:
        files = collect_pyfile(path)
        if files:
            py_files.extend(files)
            logger.debug("Found %d Python files in %s", len(files), path)
        else:
            logger.warning("No Python files found in %s", path)
    
    # 过滤 __init__.py 文件
    py_files = [file for file in py_files if not file.endswith("__init__.py")]
    logger.info("Loaded %d task files", len(py_files))
    
    return py_files
