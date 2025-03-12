from logging import getLogger, StreamHandler, Formatter
from typing import Optional
import ibevent.events
from ib_async import IB
from ibkr_event_daemon.config import Config
from ibkr_event_daemon.config import IBConfig
from ibkr_event_daemon.utils import load_hook
from ibkr_event_daemon.utils import prepare_task_path

ib:Optional[IB] = None
def current_ib(config:IBConfig)->Optional[IB]:
    global ib
    if not ib:
        
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
        self.init_task_modules()  # 初始化任务模块
        self.logger.info("Starting IB daemon...")
        self.logger.info(f"Loaded {len(self.task_modules)} task modules")
        self._ib.run()

if __name__ == "__main__":
    import os
    # 配置日志
    logger = getLogger()
    handler = StreamHandler()
    formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel("DEBUG")
    
    os.environ["IB_DAEMON_TASKS"] = r"D:\\Vscode\\ibkr_event_daemon\\ibkr_event_daemon\\tasks"
    daemon = IBDameon()
    daemon.run()
