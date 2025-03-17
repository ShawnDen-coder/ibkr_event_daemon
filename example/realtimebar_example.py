from ib_async import IB
from ibkr_event_daemon.core import LoggerType
from ib_async import contract,Forex

def setup(ib: IB,logger: LoggerType)->None:
    logger.info(f"register setup func : {__name__}")
    usd_jpy = Forex('USDJPY')   
    bars = ib.reqRealTimeBars(usd_jpy,barSize=5,whatToShow="MIDPOINT",useRTH=True)
    bars.updateEvent += onBarUpdate
    print(ib.isConnected())

def onBarUpdate(bars,hasNewBar):
    if hasNewBar:
        print(bars[-1])