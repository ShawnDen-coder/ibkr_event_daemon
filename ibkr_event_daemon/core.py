from typing import Protocol

from ib_async import IB
from loguru import logger
from typing_extensions import Optional

from ibkr_event_daemon import utils
from ibkr_event_daemon.config import IbkrSettings


LoggerType = logger.__class__

class HookModule(Protocol):
    def setup(self,ib: IB, logger: LoggerType)->None:
        ...



class IBKRClient:
    def __init__(self,ib:Optional[IB]=None,config:IbkrSettings = IbkrSettings):
        self.ib:IB = ib or IB()
        self.config = config()

    def _setup_ib_session(self):
        logger.info("start connect TWS ...")
        _config = self.config.model_dump(by_alias=True, exclude="paths")
        logger.debug(f"loading ibkr config: {_config}")
        self.ib.connect(**_config)

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

if __name__ =="__main__":
    import sys
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")
    
    ib = IBKRClient()
    ib.excute()
