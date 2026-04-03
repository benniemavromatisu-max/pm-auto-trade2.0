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
        self._price_lock = asyncio.Lock()

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
        self.state = TraderState.IDLE  # 重置状态，确保新市场能正常进入 LISTENING

        tokens = await self.market_info.get_token_ids(slug)
        if tokens:
            self.market.yes_token, self.market.no_token = tokens

            # Switch price poller to new market's tokens
            if self._switch_market_callback:
                await self._switch_market_callback(slug, self.market.yes_token, self.market.no_token)

        logger.info(f"New market: {slug}, starts in {self.market.start_time - time.time():.0f}s")

        # 广播市场切换到前端
        if self.ws_handler:
            await self.ws_handler.broadcast_market_update({
                "slug": slug,
                "time_until_start": self.market.start_time - time.time(),
                "time_until_end": self.market.end_time - time.time(),
                "state": self.state.value
            })

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
            async with self._price_lock:
                yes_price = self.market.yes_price
                no_price = self.market.no_price
            buy_min = self.config.strategy.buy_price_min
            buy_max = self.config.strategy.buy_price_max

            if buy_min <= yes_price <= buy_max:
                detected_at = time.time()
                logger.info(f"[TRADE_DETECT] {self.market.slug} YES detected at price {yes_price}, time_until_start={time_until_start:.1f}s")
                await self._place_buy("YES", yes_price, detected_at)

            if buy_min <= no_price <= buy_max:
                detected_at = time.time()
                logger.info(f"[TRADE_DETECT] {self.market.slug} NO detected at price {no_price}, time_until_start={time_until_start:.1f}s")
                await self._place_buy("NO", no_price, detected_at)

    async def _place_buy(self, direction: str, price: float, detected_at: float = None):
        token_id = self.market.yes_token if direction == "YES" else self.market.no_token
        amount = self.config.strategy.buy_amount
        slippage = self.config.strategy.slippage
        buy_price = self.order_service.calculate_buy_price(price, slippage)

        if detected_at is None:
            detected_at = time.time()

        logger.info(f"[TRADE_REQUEST] {direction} buying at {buy_price} (price: {price}, slippage: {slippage})")

        order_start = time.time()
        result = await self.order_service.place_market_buy(
            token_id=token_id,
            amount=amount,
            price=buy_price,
            side="BUY"
        )
        order_end = time.time()
        order_duration = order_end - order_start

        if result and result.get("success"):
            total_duration = order_end - detected_at
            self.market.current_round += 1
            order_id = result.get("orderID", "")

            logger.info(f"[TRADE_RESULT] {direction} BUY SUCCESS orderID={order_id}, "
                        f"detect_to_order={total_duration:.3f}s, order_request={order_duration:.3f}s")

            # Broadcast timing info to frontend
            if self.ws_handler:
                await self.ws_handler.broadcast_trade_update({
                    "timestamp": int(time.time()),
                    "side": "BUY",
                    "direction": direction,
                    "price": buy_price,
                    "amount": amount,
                    "exit_reason": None,
                    "pnl": None,
                    "timing": {
                        "detect_to_order": round(total_duration, 3),
                        "order_request": round(order_duration, 3)
                    }
                })

            new_position = Position(
                direction=direction,
                buy_price=buy_price,
                buy_order_id=order_id,
                amount=amount,
                created_at=time.time(),
                stop_loss=self.config.strategy.stop_loss,
                take_profit=self.config.strategy.take_profit
            )
            self.market.positions.append(new_position)

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
            self.trade_log.save()

            logger.info(f"Bought {direction} at {buy_price}, position created")
        else:
            error_msg = f"买入失败: {direction} 价格 {buy_price}"
            logger.warning(error_msg)
            if self.ws_handler:
                await self.ws_handler.broadcast_error(error_msg)

    async def _check_exit_conditions(self):
        now = time.time()
        time_until_end = self.market.end_time - now
        force_close = time_until_end <= self.config.strategy.force_close_minutes * 60

        async with self._price_lock:
            yes_price = self.market.yes_price
            no_price = self.market.no_price

        # 检查 YES 方向
        for position in self.market.positions:
            if position.direction == "YES" and position.status == "open":
                if force_close or yes_price >= position.take_profit or yes_price <= position.stop_loss:
                    await self._close_all_positions("YES", force_close, yes_price, no_price)
                    return

        # 检查 NO 方向
        for position in self.market.positions:
            if position.direction == "NO" and position.status == "open":
                if force_close or no_price >= position.take_profit or no_price <= position.stop_loss:
                    await self._close_all_positions("NO", force_close, yes_price, no_price)
                    return

    async def _close_all_positions(self, direction: str, force_close: bool, yes_price: float, no_price: float):
        """关闭指定方向的所有仓位，使用总余额一次性卖出。"""
        token_id = self.market.yes_token if direction == "YES" else self.market.no_token
        current_price = yes_price if direction == "YES" else no_price
        reason = "force_close" if force_close else ("take_profit" if current_price >= 0.5 else "stop_loss")
        if current_price >= 0.5:
            reason = "take_profit"
        else:
            reason = "stop_loss"

        detected_at = time.time()

        # 获取总余额
        actual_shares = await self.order_service.get_token_shares(token_id)
        if actual_shares <= 0:
            logger.warning(f"No shares to sell for {direction}")
            return

        slippage = self.config.strategy.slippage
        sell_price = self.order_service.calculate_sell_price(current_price, slippage)

        logger.info(f"[TRADE_REQUEST] {direction} closing all positions, shares={actual_shares}, price={sell_price}, reason={reason}")

        sell_start = time.time()
        result = await self.order_service.place_market_sell(
            token_id=token_id,
            amount=actual_shares,
            price=sell_price,
            side="SELL"
        )
        sell_end = time.time()

        if result and result.get("success"):
            total_duration = sell_end - detected_at
            # 更新所有该方向的仓位为 closed
            new_positions = [
                Position(
                    direction=p.direction,
                    buy_price=p.buy_price,
                    buy_order_id=p.buy_order_id,
                    amount=p.amount,
                    sell_order_id=result.get("orderID", "") if p.direction == direction else p.sell_order_id,
                    status="closed" if p.direction == direction else p.status,
                    created_at=p.created_at,
                    stop_loss=p.stop_loss,
                    take_profit=p.take_profit
                )
                for p in self.market.positions
            ]
            self.market.positions = new_positions

            pnl = (sell_price - (current_price / (1 + slippage))) * actual_shares  # 简化计算

            logger.info(f"[TRADE_RESULT] {direction} CLOSED ALL positions, orderID={result.get('orderID', '')}, "
                        f"detect_to_sell={total_duration:.3f}s, sell_request={sell_end-sell_start:.3f}s")

            if self.ws_handler:
                await self.ws_handler.broadcast_trade_update({
                    "timestamp": int(time.time()),
                    "side": "SELL",
                    "direction": direction,
                    "price": sell_price,
                    "amount": actual_shares,
                    "exit_reason": reason,
                    "pnl": pnl,
                    "timing": {
                        "detect_to_sell": round(total_duration, 3),
                        "sell_request": round(sell_end - sell_start, 3)
                    }
                })

            logger.info(f"Closed all {direction} positions at {sell_price}, PnL: {pnl:.2f}")

    async def _close_position(self, position: Position, reason: str):
        token_id = self.market.yes_token if position.direction == "YES" else self.market.no_token
        detected_at = time.time()

        # Hold lock for entire close operation to prevent race condition
        async with self._price_lock:
            current_price = self.market.yes_price if position.direction == "YES" else self.market.no_price
            sell_price = self.order_service.calculate_sell_price(current_price, self.config.strategy.slippage)

        # 获取链上实际份额 (outside lock to avoid blocking)
        actual_shares = await self.order_service.get_token_shares(token_id)
        if actual_shares <= 0:
            logger.warning(f"No shares to sell for {position.direction}")
            return

        logger.info(f"[TRADE_REQUEST] {position.direction} selling at {sell_price}, shares={actual_shares}, reason={reason}")

        sell_start = time.time()
        result = await self.order_service.place_market_sell(
            token_id=token_id,
            amount=actual_shares,
            price=sell_price,
            side="SELL"
        )
        sell_end = time.time()
        sell_duration = sell_end - sell_start

        if result and result.get("success"):
            total_duration = sell_end - detected_at
            new_status = "closed" if reason == "force_close" else "sold"
            # Use immutable update - create new positions list
            new_positions = [
                Position(
                    direction=p.direction,
                    buy_price=p.buy_price,
                    buy_order_id=p.buy_order_id,
                    amount=p.amount,
                    sell_order_id=result.get("orderID", "") if p == position else p.sell_order_id,
                    status=new_status if p == position else p.status,
                    created_at=p.created_at,
                    stop_loss=p.stop_loss,
                    take_profit=p.take_profit
                )
                for p in self.market.positions
            ]
            self.market.positions = new_positions

            pnl = (sell_price - position.buy_price) * actual_shares

            logger.info(f"[TRADE_RESULT] {position.direction} SELL SUCCESS orderID={result.get('orderID', '')}, "
                        f"detect_to_sell={total_duration:.3f}s, sell_request={sell_duration:.3f}s")

            self.trade_log.add_sell_record(
                timestamp=int(time.time()),
                market_slug=self.market.slug,
                direction=position.direction,
                price=sell_price,
                amount=actual_shares,
                order_id=position.sell_order_id,
                status="filled",
                exit_reason=reason,
                pnl=pnl
            )
            self.trade_log.save()

            if self.ws_handler:
                await self.ws_handler.broadcast_trade_update({
                    "timestamp": int(time.time()),
                    "side": "SELL",
                    "direction": position.direction,
                    "price": sell_price,
                    "amount": actual_shares,
                    "exit_reason": reason,
                    "pnl": pnl,
                    "timing": {
                        "detect_to_sell": round(total_duration, 3),
                        "sell_request": round(sell_duration, 3)
                    }
                })

            logger.info(f"Closed {position.direction} at {sell_price}, PnL: {pnl:.2f}")
        else:
            error_msg = f"卖出失败: {position.direction} 价格 {sell_price} 原因 {reason}"
            logger.warning(error_msg)
            if self.ws_handler:
                await self.ws_handler.broadcast_error(error_msg)

    async def update_prices(self, yes_price: float, no_price: float):
        """由 PricePoller 调用，更新当前市场价格。"""
        async with self._price_lock:
            self.market.yes_price = yes_price
            self.market.no_price = no_price

        # 广播价格更新到前端
        if self.ws_handler:
            now = time.time()
            time_until_start = self.market.start_time - now
            time_until_end = self.market.end_time - now
            await self.ws_handler.broadcast_market_update({
                "yes_price": yes_price,
                "no_price": no_price,
                "time_until_start": time_until_start,
                "time_until_end": time_until_end,
                "state": self.state.value
            })

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