import pytest

def test_integration_imports():
    """Verify all modules can be imported."""
    from server.config import ConfigManager
    from server.credentials import CredentialsManager
    from server.market_info import MarketInfoManager
    from server.price_poller import PricePoller
    from server.order_service import OrderService
    from server.trade_log import TradeLog
    from server.auto_trader import AutoTrader
    from server.websocket_handler import WSHandler
    assert True