"""Order service for placing and managing orders using py-clob-client."""
import asyncio
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from typing import Optional, Dict, Any, Callable
from enum import Enum
import httpx

from py_clob_client.client import ClobClient
from py_clob_client.clob_types import MarketOrderArgs, OrderType


def _round_price(price: float) -> float:
    """Round price to 2 decimal places using Decimal to avoid float precision issues."""
    return float(Decimal(str(price)).quantize(Decimal("0.01"), rounding=ROUND_DOWN))


class OrderType(Enum):
    FOK = "FOK"
    GTC = "GTC"
    FAK = "FAK"


@dataclass
class Position:
    """Represents an open position."""
    direction: str
    buy_price: float
    buy_order_id: str
    amount: float
    sell_order_id: Optional[str] = None
    status: str = "open"
    created_at: float = 0
    stop_loss: float = 13
    take_profit: float = 35


class OrderService:
    """Service for placing orders with retry logic using py-clob-client."""

    CLOB_API = "https://clob.polymarket.com"
    ORDER_TIMEOUT = 5
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    SIGNATURE_TYPE = 1  # POLY_PROXY
    FEE_RATE_BPS = 1000  # 10% taker fee

    def __init__(self, credentials, signature_type: int = 1):
        self.credentials = credentials
        self.signature_type = signature_type
        self._client: Optional[ClobClient] = None
        self._nonce = 0
        self._nonce_lock = asyncio.Lock()

    async def _get_client(self) -> ClobClient:
        """Get or create authenticated ClobClient."""
        if self._client is not None:
            return self._client

        private_key = self.credentials.private_key
        funder_address = self.credentials.funder_address

        if not private_key or not funder_address:
            raise ValueError("Missing POLY_PRIVATE_KEY or POLY_FUNDER_ADDRESS")

        # Step 1: Create temp client to derive L2 credentials
        temp_client = ClobClient(
            host=self.CLOB_API,
            chain_id=137,
            key=private_key,
            signature_type=self.signature_type,
            funder=funder_address,
        )

        # Derive L2 credentials via L1 auth
        api_creds = temp_client.create_or_derive_api_creds()

        # Step 2: Create authenticated client with L2 credentials
        self._client = ClobClient(
            host=self.CLOB_API,
            chain_id=137,
            key=private_key,
            creds=api_creds,
            signature_type=self.signature_type,
            funder=funder_address,
        )

        return self._client

    async def get_next_nonce(self) -> int:
        async with self._nonce_lock:
            self._nonce += 1
            return self._nonce

    @staticmethod
    def calculate_buy_price(current_price: float, slippage: float) -> float:
        return round(current_price * (1 + slippage), 2)

    @staticmethod
    def calculate_sell_price(current_price: float, slippage: float) -> float:
        return round(current_price * (1 - slippage), 2)

    async def place_market_buy(
        self,
        token_id: str,
        amount: float,
        price: float,
        side: str = "BUY"
    ) -> Optional[Dict[str, Any]]:
        """Place a market buy order."""
        price_rounded = _round_price(price)

        for attempt in range(self.MAX_RETRIES):
            try:
                client = await self._get_client()

                order_args = MarketOrderArgs(
                    token_id=token_id,
                    amount=amount,
                    side=side.upper(),
                    price=price_rounded,
                    fee_rate_bps=self.FEE_RATE_BPS,
                )

                signed_order = client.create_market_order(order_args)
                result = client.post_order(signed_order, OrderType.FOK)

                if result and result.get("success"):
                    return result

                error_msg = result.get("errorMsg") or result.get("error") if result else "No result"
                print(f"Buy order attempt {attempt + 1} failed: {error_msg}")

            except Exception as e:
                print(f"Buy order attempt {attempt + 1} failed: {e}")

            if attempt < self.MAX_RETRIES - 1:
                await asyncio.sleep(self.RETRY_DELAY)

        return None

    async def place_market_sell(
        self,
        token_id: str,
        amount: float,
        price: float,
        side: str = "SELL"
    ) -> Optional[Dict[str, Any]]:
        """Place a market sell order."""
        price_rounded = _round_price(price)

        for attempt in range(self.MAX_RETRIES):
            try:
                client = await self._get_client()

                order_args = MarketOrderArgs(
                    token_id=token_id,
                    amount=amount,
                    side=side.upper(),
                    price=price_rounded,
                    fee_rate_bps=self.FEE_RATE_BPS,
                )

                signed_order = client.create_market_order(order_args)
                result = client.post_order(signed_order, OrderType.FOK)

                if result and result.get("success"):
                    return result

                error_msg = result.get("errorMsg") or result.get("error") if result else "No result"
                print(f"Sell order attempt {attempt + 1} failed: {error_msg}")

            except Exception as e:
                print(f"Sell order attempt {attempt + 1} failed: {e}")

            if attempt < self.MAX_RETRIES - 1:
                await asyncio.sleep(self.RETRY_DELAY)

        return None
