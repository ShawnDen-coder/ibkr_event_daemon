import glob
import importlib
import os
from typing import Optional

from loguru import logger


def load_hook(file_path):  # noqa: D103
    try:
        spec = importlib.util.spec_from_file_location("hook", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logger.error("Failed to load hook from %s: %s", file_path, str(e))
        return None


def collect_pyfile(path: str) -> Optional[list[str]]:  # noqa: D103
    if os.path.isdir(path):
        pattern = os.path.join(path, "**", "*.py")
        return glob.glob(pattern, recursive=True)
    elif os.path.isfile(path) and path.endswith(".py"):
        return [path]
    return None


def prepare_task_path(env_key: str = "IBKR_DAEMON_TASKS") -> list[str]:  # noqa: D103
    env_data: list[str] = os.getenv(env_key, "").split(os.pathsep)
    env_data = [path for path in env_data if os.path.exists(path)]
    py_files: list[str] = []
    for path in env_data:
        py_files.extend(collect_pyfile(path))
    py_files = [file for file in py_files if not file.endswith("__init__.py")]
    return py_files
