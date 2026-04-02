"""Main entry point for the trading server."""
import asyncio
import signal
from server.config import ConfigManager
from server.credentials import CredentialsManager
from server.market_info import MarketInfoManager
from server.price_poller import PricePoller
from server.order_service import OrderService
from server.trade_log import TradeLog
from server.auto_trader import AutoTrader
from server.websocket_handler import WSHandler


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
        self._running = False

    async def start(self):
        self._running = True
        print("Starting trading server...")

        # Auto-fetch L2 credentials via L1 auth if not already saved
        await self.credentials.fetch_and_save_l2_credentials()

        self.auto_trader.set_websocket_handler(self.ws_handler)
        self.ws_handler.set_auto_trader(self.auto_trader)

        await self.ws_handler.start()

        current_slug = self.market_info.get_current_slug()
        tokens = await self.market_info.get_token_ids(current_slug)
        if tokens:
            yes_token, no_token = tokens
            print(f"Market: {current_slug}")
            print(f"YES token: {yes_token}")
            print(f"NO token: {no_token}")

            self.price_poller = PricePoller(
                yes_token=yes_token,
                no_token=no_token,
                price_callback=lambda y, n: self.auto_trader.update_prices(y, n)
            )

        asyncio.create_task(self.auto_trader.start())

        if self.price_poller:
            asyncio.create_task(self.price_poller.start())

        print("Trading server started successfully")

        while self._running:
            await asyncio.sleep(1)

    async def stop(self):
        self._running = False
        print("Stopping trading server...")

        if self.price_poller:
            await self.price_poller.stop()

        await self.ws_handler.stop()
        await self.auto_trader.stop()

        print("Trading server stopped")


async def main():
    server = TradingServer()

    loop = asyncio.get_event_loop()

    def signal_handler():
        asyncio.create_task(server.stop())

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    try:
        await server.start()
    except KeyboardInterrupt:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
