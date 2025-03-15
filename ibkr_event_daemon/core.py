from typing import Protocol

from ib_async import IB
from loguru import logger
from typing_extensions import Optional

from ibkr_event_daemon import utils


LoggerType = logger.__class__

class HookModule(Protocol):
    def setup(self,ib: IB, logger: LoggerType)->None:
        ...



class IBKRClient:
    def __init__(self,ib:IB):
        self.ib:IB = ib or IB()

    def _setup_ib_session(self):
        logger.info("start connect TWS ...")
        self.ib.connect("127.0.0.1",7497)

    def _setup_callback(self):
        files = utils.prepare_task_path()
        for item in files:
            moudle:Optional[HookModule] = utils.load_hook(item)
            if not moudle:
                continue
            try:
                moudle.setup(self.ib, logger)
                logger.info(f"setup callback func {moudle.__name__}")
            except AttributeError as e:
                logger.exception(f"load moudle {moudle.__name__} error: \n {e}")

    def setup(self):
        if not self.ib.isConnected:
            self._setup_ib_session()
        self._setup_callback()

    def pre_action(self):
        self.setup()

    def stop(self):
        logger.info("Stopping the IBKR daemon ...")
        self.ib.disconnect()

    def excute(self)->None:
        try:
            self.pre_action()
            self.ib.run()
        except KeyboardInterrupt:
            self.stop()
            logger.info("Program interrupted and stopped.")
