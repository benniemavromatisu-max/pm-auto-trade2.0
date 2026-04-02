"""REST API 价格轮询器，替代 WebSocket 获取价格。"""
import asyncio
import httpx
from typing import Callable, Tuple, Awaitable

from server.server_logger import get_logger

logger = get_logger("price_poller")

CLOB_API = "https://clob.polymarket.com"


class PricePoller:
    """REST API 价格轮询器，每500ms获取一次价格。"""

    POLL_INTERVAL = 0.5  # 500ms

    def __init__(self, yes_token: str, no_token: str, price_callback: Callable[[float, float], Awaitable[None]]):
        self.yes_token = yes_token
        self.no_token = no_token
        self.price_callback = price_callback  # 回调接收 (yes_price, no_price)
        self._running = False
        self._yes_price = 0.0
        self._no_price = 0.0

    async def start(self):
        """启动轮询循环。"""
        self._running = True
        while self._running:
            await self._fetch_prices()
            await asyncio.sleep(self.POLL_INTERVAL)

    async def stop(self):
        """停止轮询。"""
        self._running = False

    async def _fetch_prices(self):
        """从 REST API 获取价格。"""
        payload = [
            {"token_id": self.yes_token, "side": "BUY"},
            {"token_id": self.no_token, "side": "SELL"}
        ]
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"{CLOB_API}/prices",
                    json=payload,
                    timeout=5.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    yes_price = float(data.get(self.yes_token, {}).get("BUY", 0.0))
                    no_price = float(data.get(self.no_token, {}).get("SELL", 0.0))
                    self._yes_price = yes_price
                    self._no_price = no_price
                    asyncio.create_task(self.price_callback(yes_price, no_price))
                else:
                    logger.warning(f"Price fetch failed: {resp.status_code}")
            except Exception as e:
                logger.warning(f"Price fetch error: {e}")

    @property
    def prices(self) -> Tuple[float, float]:
        """返回当前缓存的价格 (yes, no)。"""
        return (self._yes_price, self._no_price)