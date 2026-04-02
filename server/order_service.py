"""Order service for placing and managing orders."""
import asyncio
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum
import httpx


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
    """Service for placing orders with retry logic."""

    CLOB_API = "https://clob.polymarket.com"
    ORDER_TIMEOUT = 5
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    def __init__(self, credentials, signature_type: int = 1):
        self.credentials = credentials
        self.signature_type = signature_type
        self._nonce = 0
        self._nonce_lock = asyncio.Lock()

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
        order_data = {
            "order": {
                "maker": self.credentials.funder_address,
                "signer": self.credentials.funder_address,
                "taker": "0x0000000000000000000000000000000000000000",
                "tokenId": token_id,
                "makerAmount": str(int(amount * 1e6)),
                "takerAmount": str(int(amount * price * 1e6)),
                "side": side,
                "expiration": str(int(asyncio.get_event_loop().time()) + 300),
                "nonce": str(await self.get_next_nonce()),
                "feeRateBps": "30",
                "signature": "",
                "salt": 0,
                "signatureType": self.signature_type
            },
            "owner": self.credentials.api_key,
            "orderType": OrderType.FOK.value,
            "deferExec": False
        }

        for attempt in range(self.MAX_RETRIES):
            try:
                result = await self._submit_order(order_data)
                if result and result.get("success"):
                    return result
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
        order_data = {
            "order": {
                "maker": self.credentials.funder_address,
                "signer": self.credentials.funder_address,
                "taker": "0x0000000000000000000000000000000000000000",
                "tokenId": token_id,
                "makerAmount": str(int(amount * 1e6)),
                "takerAmount": str(int(amount * price * 1e6)),
                "side": side,
                "expiration": str(int(asyncio.get_event_loop().time()) + 300),
                "nonce": str(await self.get_next_nonce()),
                "feeRateBps": "30",
                "signature": "",
                "salt": 0,
                "signatureType": self.signature_type
            },
            "owner": self.credentials.api_key,
            "orderType": OrderType.FOK.value,
            "deferExec": False
        }

        for attempt in range(self.MAX_RETRIES):
            try:
                result = await self._submit_order(order_data)
                if result and result.get("success"):
                    return result
            except Exception as e:
                print(f"Sell order attempt {attempt + 1} failed: {e}")

            if attempt < self.MAX_RETRIES - 1:
                await asyncio.sleep(self.RETRY_DELAY)

        return None

    async def _submit_order(self, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        headers = {
            "POLY_API_KEY": self.credentials.api_key,
            "POLY_ADDRESS": self.credentials.funder_address,
            "POLY_PASSPHRASE": self.credentials.api_passphrase,
            "POLY_TIMESTAMP": str(int(asyncio.get_event_loop().time())),
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.CLOB_API}/order",
                json=order_data,
                headers=headers,
                timeout=self.ORDER_TIMEOUT
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Order failed: {response.status_code} - {response.text}")
                return None