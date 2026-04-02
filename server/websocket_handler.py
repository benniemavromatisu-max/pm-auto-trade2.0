"""WebSocket handler for frontend communication."""
import asyncio
import json
import websockets
from typing import Set, Optional, Dict, Any

from server.server_logger import get_logger

logger = get_logger("websocket")


class WSHandler:
    """Handles WebSocket connections with frontend clients."""

    def __init__(self, host: str = "localhost", port: int = 8766):
        self.host = host
        self.port = port
        self._clients: Set[websockets.WebSocketServerProtocol] = set()
        self._running = False
        self._server = None
        self.auto_trader = None

    def set_auto_trader(self, auto_trader):
        self.auto_trader = auto_trader

    async def start(self):
        self._running = True
        self._server = await websockets.serve(self._handle_client, self.host, self.port)
        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")

    async def stop(self):
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        logger.info("WebSocket server stopped")

    async def _handle_client(self, websocket):
        self._clients.add(websocket)
        try:
            async for message in websocket:
                await self._process_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self._clients.remove(websocket)

    async def _process_message(self, websocket, message: str):
        try:
            data = json.loads(message)
            msg_type = data.get("type", "")

            if msg_type == "get_config":
                await self._send_config(websocket)
            elif msg_type == "update_config":
                await self._update_config(data.get("data", {}))
                await self._broadcast_status()
            elif msg_type == "get_status":
                await self._send_status(websocket)
        except json.JSONDecodeError:
            pass

    async def _send_config(self, websocket):
        if self.auto_trader:
            config = self.auto_trader.config.config
            await websocket.send(json.dumps({
                "type": "config",
                "data": {
                    "strategy": {
                        "buy_price_min": config.strategy.buy_price_min,
                        "buy_price_max": config.strategy.buy_price_max,
                        "stop_loss": config.strategy.stop_loss,
                        "take_profit": config.strategy.take_profit,
                        "slippage": config.strategy.slippage,
                        "buy_window_minutes": config.strategy.buy_window_minutes,
                        "force_close_minutes": config.strategy.force_close_minutes,
                        "rounds_per_market": config.strategy.rounds_per_market,
                        "buy_amount": config.strategy.buy_amount,
                    }
                }
            }))

    async def _update_config(self, data: Dict[str, Any]):
        if self.auto_trader and "strategy" in data:
            strategy = data["strategy"]
            config = self.auto_trader.config.config.strategy
            for key, value in strategy.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            self.auto_trader.config.save()

    async def _send_status(self, websocket):
        if self.auto_trader:
            status = await self.auto_trader.get_status()
            await websocket.send(json.dumps({
                "type": "status",
                "data": status
            }))

    async def _broadcast_status(self):
        if self.auto_trader:
            status = await self.auto_trader.get_status()
            message = json.dumps({
                "type": "status",
                "data": status
            })
            await asyncio.gather(
                *[client.send(message) for client in self._clients],
                return_exceptions=True
            )

    async def broadcast_market_update(self, data: Dict[str, Any]):
        message = json.dumps({
            "type": "market_update",
            "data": data
        })
        await asyncio.gather(
            *[client.send(message) for client in self._clients],
            return_exceptions=True
        )

    async def broadcast_trade_update(self, data: Dict[str, Any]):
        message = json.dumps({
            "type": "trade_update",
            "data": data
        })
        await asyncio.gather(
            *[client.send(message) for client in self._clients],
            return_exceptions=True
        )