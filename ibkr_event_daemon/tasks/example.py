from ibkr_event_daemon.core import ib
from ib_async.contract import Contract
from ibevent.events import IBEventType

usd_jpy = Contract('USDJPY')
@ib.events.register(
    IBEventType.BAR_UPDATE,
    bind_to=ib.reqRealTimeBars(
        usd_jpy,
        barSize=5,
        whatToShow='MIDPOINT',
        useRTH=True
    )
)
def on_bar_update(ib,bars,has_new_bar):
    if has_new_bar:
        print(bars[-1])