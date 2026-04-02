"""Trade logging service."""
import json
import os
from typing import List, Dict, Any, Optional
from datetime import date


class TradeLog:
    """Manages trade records with daily files."""

    def __init__(self, base_path: str = None):
        if base_path is None:
            base_path = os.path.join(os.path.dirname(__file__), "..", "data", "trades")
        self.base_path = base_path
        self.trades: List[Dict[str, Any]] = []
        self._ensure_directory()

    def _ensure_directory(self):
        os.makedirs(self.base_path, exist_ok=True)

    def _get_filename(self, trade_date: date = None) -> str:
        if trade_date is None:
            trade_date = date.today()
        return f"trades-{trade_date.isoformat()}.json"

    def _get_filepath(self, trade_date: date = None) -> str:
        return os.path.join(self.base_path, self._get_filename(trade_date))

    def add_trade(self, trade: Dict[str, Any]):
        self.trades.append(trade)

    def save(self, trade_date: date = None):
        filepath = self._get_filepath(trade_date)
        data = {
            "date": (trade_date or date.today()).isoformat(),
            "trades": self.trades
        }
        tmp_path = filepath + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, filepath)

    def load(self, trade_date: date = None):
        filepath = self._get_filepath(trade_date)
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                data = json.load(f)
                self.trades = data.get("trades", [])
        else:
            self.trades = []

    def get_today_trades(self) -> List[Dict[str, Any]]:
        self.load()
        return self.trades

    def add_buy_record(
        self,
        timestamp: int,
        market_slug: str,
        round_num: int,
        direction: str,
        price: float,
        amount: float,
        order_id: str,
        status: str = "filled"
    ):
        self.add_trade({
            "timestamp": timestamp,
            "market_slug": market_slug,
            "round": round_num,
            "side": "BUY",
            "direction": direction,
            "price": price,
            "amount": amount,
            "order_id": order_id,
            "status": status,
            "exit_reason": None,
            "pnl": None
        })

    def add_sell_record(
        self,
        timestamp: int,
        market_slug: str,
        direction: str,
        price: float,
        amount: float,
        order_id: str,
        status: str,
        exit_reason: str,
        pnl: float
    ):
        self.add_trade({
            "timestamp": timestamp,
            "market_slug": market_slug,
            "round": 0,
            "side": "SELL",
            "direction": direction,
            "price": price,
            "amount": amount,
            "order_id": order_id,
            "status": status,
            "exit_reason": exit_reason,
            "pnl": pnl
        })
