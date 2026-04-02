import pytest
from server.auto_trader import AutoTrader, TraderState, MarketState

def test_trader_state_enum():
    assert TraderState.IDLE.value == "IDLE"
    assert TraderState.LISTENING.value == "LISTENING"
    assert TraderState.MONITORING.value == "MONITORING"
    assert TraderState.DONE.value == "DONE"

def test_auto_trader_init():
    from server.config import ConfigManager
    from server.market_info import MarketInfoManager
    from server.order_service import OrderService
    from server.trade_log import TradeLog
    from server.credentials import CredentialsManager

    config = ConfigManager()
    credentials = CredentialsManager()
    market_info = MarketInfoManager()
    order_service = OrderService(credentials)
    trade_log = TradeLog()

    trader = AutoTrader(config, market_info, order_service, trade_log)
    assert trader.state == TraderState.IDLE