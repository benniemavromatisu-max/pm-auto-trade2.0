"""Auto-trader state machine for trading logic."""
import asyncio
import time
from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass, field

from server.config import ConfigManager
from server.market_info import MarketInfoManager, get_current_slug, get_slug_end_timestamp, get_slug_start_timestamp
from server.order_service import OrderService, Position
from server.trade_log import TradeLog
from server.server_logger import get_logger

logger = get_logger("auto_trader")


class TraderState(Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    MONITORING = "MONITORING"
    DONE = "DONE"


@dataclass
class MarketState:
    slug: str = ""
    start_time: float = 0
    end_time: float = 0
    yes_price: float = 0
    no_price: float = 0
    yes_token: str = ""
    no_token: str = ""
    current_round: int = 0
    positions: List[Position] = field(default_factory=list)


class AutoTrader:
    """State machine for automated trading."""

    PRICE_CHECK_INTERVAL = 0.5  # 500ms，与 PricePoller 同步

    def __init__(
        self,
        config: ConfigManager,
        market_info: MarketInfoManager,
        order_service: OrderService,
        trade_log: TradeLog,
        ws_handler=None
    ):
        self.config = config
        self.market_info = market_info
        self.order_service = order_service
        self.trade_log = trade_log
        self.ws_handler = ws_handler
        self._switch_market_callback = None

        self.state = TraderState.IDLE
        self.market = MarketState()
        self._running = False
        self._trade_count = 0

    def set_websocket_handler(self, ws_handler):
        self.ws_handler = ws_handler

    def set_switch_market_callback(self, callback):
        """Set callback to be called when market switches."""
        self._switch_market_callback = callback

    async def start(self):
        self._running = True
        await self._run()

    async def stop(self):
        self._running = False

    async def _run(self):
        while self._running:
            current_slug = get_current_slug()

            if current_slug != self.market.slug:
                await self._init_market(current_slug)

            now = time.time()
            time_until_start = self.market.start_time - now
            time_until_end = self.market.end_time - now

            if self.state == TraderState.IDLE:
                if time_until_start <= self.config.strategy.buy_window_minutes * 60:
                    await self._enter_listening()

            elif self.state == TraderState.LISTENING:
                if time_until_start <= 0:
                    await self._check_entries()
                    if self.market.current_round >= self.config.strategy.rounds_per_market:
                        self.state = TraderState.MONITORING

            elif self.state == TraderState.MONITORING:
                await self._check_exit_conditions()

            elif self.state == TraderState.DONE:
                if time_until_end <= 0:
                    self.state = TraderState.IDLE
                    self.market.slug = ""
                    self._trade_count = 0

            await asyncio.sleep(self.PRICE_CHECK_INTERVAL)

    async def _init_market(self, slug: str):
        self.market.slug = slug
        self.market.end_time = get_slug_end_timestamp(slug)
        self.market.start_time = get_slug_start_timestamp(slug)
        self.market.current_round = 0
        self.market.positions = []
        self.market.yes_price = 0
        self.market.no_price = 0

        tokens = await self.market_info.get_token_ids(slug)
        if tokens:
            self.market.yes_token, self.market.no_token = tokens

            # Switch price poller to new market's tokens
            if self._switch_market_callback:
                await self._switch_market_callback(slug, self.market.yes_token, self.market.no_token)

        logger.info(f"New market: {slug}, starts in {self.market.start_time - time.time():.0f}s")

    async def _enter_listening(self):
        self.state = TraderState.LISTENING
        self.market.current_round = 0
        logger.info(f"Entering LISTENING state for {self.market.slug}")

    async def _check_entries(self):
        if self.market.current_round >= self.config.strategy.rounds_per_market:
            return

        now = time.time()
        time_until_start = self.market.start_time - now

        if time_until_start > -self.config.strategy.buy_window_minutes * 60:
            yes_price = self.market.yes_price
            no_price = self.market.no_price
            buy_min = self.config.strategy.buy_price_min
            buy_max = self.config.strategy.buy_price_max

            if buy_min <= yes_price <= buy_max:
                await self._place_buy("YES", yes_price)

            if buy_min <= no_price <= buy_max:
                await self._place_buy("NO", no_price)

    async def _place_buy(self, direction: str, price: float):
        token_id = self.market.yes_token if direction == "YES" else self.market.no_token
        amount = self.config.strategy.buy_amount
        slippage = self.config.strategy.slippage
        buy_price = self.order_service.calculate_buy_price(price, slippage)

        logger.info(f"Buying {direction} at {buy_price} (price: {price}, slippage: {slippage})")

        result = await self.order_service.place_market_buy(
            token_id=token_id,
            amount=amount,
            price=buy_price,
            side="BUY"
        )

        if result and result.get("success"):
            self.market.current_round += 1
            order_id = result.get("orderID", "")

            position = Position(
                direction=direction,
                buy_price=buy_price,
                buy_order_id=order_id,
                amount=amount,
                created_at=time.time(),
                stop_loss=self.config.strategy.stop_loss,
                take_profit=self.config.strategy.take_profit
            )
            self.market.positions.append(position)

            self.trade_log.add_buy_record(
                timestamp=int(time.time()),
                market_slug=self.market.slug,
                round_num=self.market.current_round,
                direction=direction,
                price=buy_price,
                amount=amount,
                order_id=order_id,
                status="filled"
            )

            logger.info(f"Bought {direction} at {buy_price}, position created")

    async def _check_exit_conditions(self):
        now = time.time()
        time_until_end = self.market.end_time - now
        force_close = time_until_end <= self.config.strategy.force_close_minutes * 60

        for position in self.market.positions:
            if position.status != "open":
                continue

            current_price = self.market.yes_price if position.direction == "YES" else self.market.no_price

            if force_close:
                await self._close_position(position, "force_close")
            elif current_price >= position.take_profit:
                await self._close_position(position, "take_profit")
            elif current_price <= position.stop_loss:
                await self._close_position(position, "stop_loss")

    async def _close_position(self, position: Position, reason: str):
        token_id = self.market.yes_token if position.direction == "YES" else self.market.no_token
        current_price = self.market.yes_price if position.direction == "YES" else self.market.no_price
        sell_price = self.order_service.calculate_sell_price(current_price, self.config.strategy.slippage)

        logger.info(f"Closing {position.direction} position at {sell_price} (reason: {reason})")

        result = await self.order_service.place_market_sell(
            token_id=token_id,
            amount=position.amount,
            price=sell_price,
            side="SELL"
        )

        if result and result.get("success"):
            position.status = "closed" if reason == "force_close" else "sold"
            position.sell_order_id = result.get("orderID", "")

            pnl = (sell_price - position.buy_price) * position.amount

            self.trade_log.add_sell_record(
                timestamp=int(time.time()),
                market_slug=self.market.slug,
                direction=position.direction,
                price=sell_price,
                amount=position.amount,
                order_id=position.sell_order_id,
                status="filled",
                exit_reason=reason,
                pnl=pnl
            )

            logger.info(f"Closed {position.direction} at {sell_price}, PnL: {pnl:.2f}")

    def update_prices(self, yes_price: float, no_price: float):
        """由 PricePoller 调用，更新当前市场价格。"""
        self.market.yes_price = yes_price
        self.market.no_price = no_price

    async def get_status(self) -> Dict:
        return {
            "state": self.state.value,
            "slug": self.market.slug,
            "yes_price": self.market.yes_price,
            "no_price": self.market.no_price,
            "current_round": self.market.current_round,
            "positions": [
                {
                    "direction": p.direction,
                    "buy_price": p.buy_price,
                    "status": p.status,
                    "pnl": (self.market.yes_price if p.direction == "YES" else self.market.no_price) - p.buy_price
                }
                for p in self.market.positions
            ]
        }