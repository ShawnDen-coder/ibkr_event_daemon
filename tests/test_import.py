"""Import Test."""

import importlib
import pkgutil

import ibkr_event_daemon # noqa

def test_imports():
    """Test import modules."""
    prefix = "{}.".format(ibkr_event_daemon.__name__) # noqa
    iter_packages = pkgutil.walk_packages(
        ibkr_event_daemon.__path__,  # noqa
        prefix,
    )
    for _, name, _ in iter_packages:
        module_name = name if name.startswith(prefix) else prefix + name
        importlib.import_module(module_name)