import pytest

from ibkr_event_daemon.utils import prepare_task_path,collect_pyfile


def test_prepare_task_path(mocker):
    mocker.patch("os.getenv",return_value="path/to/tasks")
    mocker.patch("os.path.exists",return_value=True)
    mocker.patch("ibkr_event_daemon.utils.collect_pyfile",return_value=[
        "path/to/tasks/task.py",
        "path/to/tasks/__init__.py"
    ])


    assert prepare_task_path() == ["path/to/tasks/task.py"]

@pytest.mark.parametrize("path,expected",[
    ("path/to/tasks",["path/to/tasks/task.py"]),
    ("path/to/tasks/task.py",["path/to/tasks/task.py"]),
])
def test_collect_pyfile(path,expected,mocker):
    if path.endswith(".py"):
        mocker.patch("os.path.isfile",return_value=True)
        mocker.patch("os.path.isdir",return_value=False)
    else:
        mocker.patch("os.path.isfile",return_value=False)
        mocker.patch("os.path.isdir",return_value=True)
        mocker.patch("glob.glob",return_value=expected)

    assert collect_pyfile(path) == expected
