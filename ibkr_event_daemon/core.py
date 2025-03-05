from ib_async import IB
from logging import getLogger
from typing import Optional
from ibkr_event_daemon.config import Config, IBConfig
from ibkr_event_daemon.utils import prepare_task_path, load_hook

_ib_instance:Optional[IB] = None

def current_ib(config:IBConfig)->Optional[IB]:
    if not _ib_instance:
        ib = IB()
        ib.connect(**config.model_dump())
    return ib

class IBDameon:
    def __init__(self):
        self.logger = getLogger(__name__)
        self.config:Config = Config()
        self._ib:Optional[IB] = current_ib(self.config.ib)
        self.task_modules = []        

    def init_task_modules(self):
        tasks_path = prepare_task_path("IB_DAEMON_TASKS")
        self.task_modules = [load_hook(file) for file in tasks_path]

    def run(self):
        self._ib.run()

if __name__ == "__main__":
    daemon = IBDameon()
    daemon.run()
