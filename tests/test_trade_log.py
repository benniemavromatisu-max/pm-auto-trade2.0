import pytest
import tempfile
import os
from datetime import date
from server.trade_log import TradeLog

def test_trade_log_save_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        log = TradeLog(tmpdir)
        log.add_trade({
            "timestamp": 1234567890,
            "market_slug": "btc-updown-5m-123",
            "round": 1,
            "side": "BUY",
            "direction": "YES",
            "price": 20.0,
            "amount": 1.0,
            "order_id": "0x123",
            "status": "filled"
        })
        log.save()

        log2 = TradeLog(tmpdir)
        log2.load()
        assert len(log2.trades) == 1
        assert log2.trades[0]["side"] == "BUY"