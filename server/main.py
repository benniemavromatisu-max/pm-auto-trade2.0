"""Main entry point for the trading server."""
import asyncio
import signal
from server.config import ConfigManager
from server.credentials import CredentialsManager
from server.market_info import MarketInfoManager, get_current_slug
from server.price_poller import PricePoller
from server.order_service import OrderService
from server.trade_log import TradeLog
from server.auto_trader import AutoTrader
from server.websocket_handler import WSHandler
from server.server_logger import get_logger

logger = get_logger("main")


class TradingServer:
    """Main trading server that orchestrates all components."""

    def __init__(self):
        self.config = ConfigManager()
        self.credentials = CredentialsManager()
        self.market_info = MarketInfoManager()
        self.order_service = OrderService(self.credentials)
        self.trade_log = TradeLog()
        self.auto_trader = AutoTrader(
            self.config,
            self.market_info,
            self.order_service,
            self.trade_log
        )
        self.ws_handler = WSHandler()
        self.price_poller = None
        self.price_poller_task = None
        self._running = False
        # Give auto_trader a callback to switch price poller on market change
        self.auto_trader.set_switch_market_callback(self._switch_price_poller)

    async def _switch_price_poller(self, slug: str, yes_token: str, no_token: str):
        """Switch price poller to new market's tokens."""
        # 取消旧的 PricePoller 任务
        if self.price_poller_task:
            self.price_poller_task.cancel()
            try:
                await self.price_poller_task
            except asyncio.CancelledError:
                pass
            self.price_poller_task = None
            logger.info("Old price poller cancelled")

        self.price_poller = PricePoller(
            yes_token=yes_token,
            no_token=no_token,
            price_callback=lambda y, n: self.auto_trader.update_prices(y, n)
        )
        self.price_poller_task = asyncio.create_task(self.price_poller.start())
        logger.info(f"Price poller switched to market: {slug}")

    async def start(self):
        self._running = True
        logger.info("Starting trading server...")

        # Auto-fetch L2 credentials via L1 auth if not already saved
        await self.credentials.fetch_and_save_l2_credentials()

        # Pre-warm order service client to avoid slow first order
        await self.order_service.warmup()

        self.auto_trader.set_websocket_handler(self.ws_handler)
        self.ws_handler.set_auto_trader(self.auto_trader)

        await self.ws_handler.start()

        current_slug = get_current_slug()
        tokens = await self.market_info.get_token_ids(current_slug)
        if tokens:
            yes_token, no_token = tokens
            logger.info(f"Market: {current_slug}")
            logger.info(f"YES token: {yes_token}")
            logger.info(f"NO token: {no_token}")

            self.price_poller = PricePoller(
                yes_token=yes_token,
                no_token=no_token,
                price_callback=lambda y, n: self.auto_trader.update_prices(y, n)
            )

        asyncio.create_task(self.auto_trader.start())

        if self.price_poller:
            self.price_poller_task = asyncio.create_task(self.price_poller.start())

        logger.info("Trading server started successfully")

        while self._running:
            await asyncio.sleep(1)

    async def stop(self):
        self._running = False
        logger.info("Stopping trading server...")

        if self.price_poller_task:
            self.price_poller_task.cancel()
            try:
                await self.price_poller_task
            except asyncio.CancelledError:
                pass

        await self.ws_handler.stop()
        await self.auto_trader.stop()

        logger.info("Trading server stopped")


async def main():
    server = TradingServer()
    loop = asyncio.get_event_loop()

    def signal_handler():
        asyncio.create_task(server.stop())

    try:
        loop.add_signal_handler(signal.SIGINT, signal_handler)
    except NotImplementedError:
        # Windows doesn't support add_signal_handler
        pass

    try:
        await server.start()
    except KeyboardInterrupt:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
