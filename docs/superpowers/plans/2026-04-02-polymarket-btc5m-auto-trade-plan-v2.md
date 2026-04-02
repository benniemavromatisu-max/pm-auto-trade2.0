# Polymarket BTC 5分钟涨跌自动交易系统实现计划 v2

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建Polymarket BTC 5分钟涨跌市场的自动交易系统，价格获取改为REST API轮询（500ms）

**Architecture:** Python异步后端 + Chrome Extension前端，后端使用REST轮询获取价格，状态机管理交易逻辑，前端通过WebSocket与后端通信。

**Tech Stack:** Python 3.11+, httpx, websockets, asyncio; Chrome Extension (Manifest V3)

**核心变更：** 移除 `market_tracker.py` (WebSocket)，新增 `price_poller.py` (REST轮询)

---

## 文件结构

```
pm-auto-trade2.0/
├── server/
│   ├── __init__.py
│   ├── main.py              # 入口，启动所有任务
│   ├── config.py            # 配置管理
│   ├── credentials.py       # 凭据加载
│   ├── market_info.py       # slug解析、市场信息获取
│   ├── price_poller.py      # REST API 价格轮询 (新增)
│   ├── auto_trader.py       # 交易状态机
│   ├── order_service.py      # 订单操作
│   ├── trade_log.py         # 交易记录
│   ├── websocket_handler.py  # 与前端通信
│   └── requirements.txt
├── extension/
│   ├── manifest.json
│   ├── icons/
│   └── sidepanel/
│       ├── index.html
│       ├── app.js
│       └── style.css
├── data/
│   ├── config.json
│   └── trades/
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_credentials.py
│   ├── test_market_info.py
│   ├── test_price_poller.py
│   ├── test_auto_trader.py
│   ├── test_order_service.py
│   ├── test_trade_log.py
│   ├── test_websocket_handler.py
│   └── test_integration.py
└── docs/superpowers/plans/
```

---

## Task 1: 项目初始化 - 依赖和目录结构

**Files:**
- Create: `server/requirements.txt`
- Create: `server/__init__.py`
- Create: `tests/__init__.py`
- Create: `data/config.json`
- Create: `data/trades/.gitkeep`

- [ ] **Step 1: Create requirements.txt**

```txt
httpx==0.27.0
websockets==12.0
python-dotenv==1.0.0
pytest==8.0.0
pytest-asyncio==0.23.0
```

- [ ] **Step 2: Create __init__.py (empty)**

```python
```

- [ ] **Step 3: Create initial config.json**

```json
{
  "strategy": {
    "buy_price_min": 18,
    "buy_price_max": 22,
    "stop_loss": 13,
    "take_profit": 35,
    "slippage": 0.10,
    "buy_window_minutes": 2,
    "force_close_minutes": 1,
    "rounds_per_market": 3,
    "buy_amount": 1.0
  },
  "credentials": {
    "private_key": "",
    "api_key": "",
    "api_secret": "",
    "api_passphrase": "",
    "funder_address": ""
  }
}
```

- [ ] **Step 4: Create .gitkeep for trades directory**

```gitkeep
```

- [ ] **Step 5: Commit**

```bash
git add server/requirements.txt server/__init__.py tests/__init__.py data/
git commit -m "chore: initial project structure"
```

---

## Task 2: 配置管理 (config.py)

**Files:**
- Create: `server/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
import pytest
import os
import tempfile
import json
from server.config import ConfigManager, StrategyConfig, validate_config

def test_strategy_config_defaults():
    cfg = StrategyConfig()
    assert cfg.buy_price_min == 18
    assert cfg.buy_price_max == 22
    assert cfg.stop_loss == 13
    assert cfg.take_profit == 35
    assert cfg.slippage == 0.10

def test_validate_config_valid():
    cfg = {
        "strategy": {
            "buy_price_min": 18,
            "buy_price_max": 22,
            "stop_loss": 13,
            "take_profit": 35,
            "slippage": 0.10,
            "buy_window_minutes": 2,
            "force_close_minutes": 1,
            "rounds_per_market": 3,
            "buy_amount": 1.0
        }
    }
    errors = validate_config(cfg)
    assert len(errors) == 0

def test_validate_config_invalid_range():
    cfg = {
        "strategy": {
            "buy_price_min": 25,
            "buy_price_max": 22,
            "stop_loss": 13,
            "take_profit": 35,
            "slippage": 0.10,
            "buy_window_minutes": 2,
            "force_close_minutes": 1,
            "rounds_per_market": 3,
            "buy_amount": 1.0
        }
    }
    errors = validate_config(cfg)
    assert len(errors) > 0

def test_config_manager_save_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = ConfigManager(tmpdir)
        cfg.strategy.buy_price_min = 20
        cfg.save()
        cfg2 = ConfigManager(tmpdir)
        cfg2.load()
        assert cfg2.strategy.buy_price_min == 20
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL - module not found

- [ ] **Step 3: Write minimal config.py**

```python
"""Configuration management for the trading bot."""
import json
import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class StrategyConfig:
    buy_price_min: float = 18
    buy_price_max: float = 22
    stop_loss: float = 13
    take_profit: float = 35
    slippage: float = 0.10
    buy_window_minutes: int = 2
    force_close_minutes: int = 1
    rounds_per_market: int = 3
    buy_amount: float = 1.0


@dataclass
class Credentials:
    private_key: str = ""
    api_key: str = ""
    api_secret: str = ""
    api_passphrase: str = ""
    funder_address: str = ""


@dataclass
class Config:
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    credentials: Credentials = field(default_factory=Credentials)


def validate_config(config: dict) -> List[str]:
    """Validate configuration and return list of errors."""
    errors = []
    if "strategy" not in config:
        errors.append("Missing 'strategy' section")
        return errors

    s = config["strategy"]
    if s.get("buy_price_min", 0) >= s.get("buy_price_max", 100):
        errors.append("buy_price_min must be < buy_price_max")
    if s.get("stop_loss", 0) >= s.get("take_profit", 100):
        errors.append("stop_loss must be < take_profit")
    if not 0 <= s.get("slippage", 0) <= 1:
        errors.append("slippage must be between 0 and 1")

    return errors


class ConfigManager:
    DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "config.json")

    def __init__(self, config_path: str = None):
        self.config_path = config_path or self.DEFAULT_PATH
        self.config = Config()
        self.load()

    def load(self):
        """Load configuration from JSON file."""
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                data = json.load(f)
                if "strategy" in data:
                    for key, value in data["strategy"].items():
                        if hasattr(self.config.strategy, key):
                            setattr(self.config.strategy, key, value)
                if "credentials" in data:
                    for key, value in data["credentials"].items():
                        if hasattr(self.config.credentials, key):
                            setattr(self.config.credentials, key, value)

    def save(self):
        """Save configuration to JSON file (atomic write)."""
        data = {
            "strategy": {
                "buy_price_min": self.config.strategy.buy_price_min,
                "buy_price_max": self.config.strategy.buy_price_max,
                "stop_loss": self.config.strategy.stop_loss,
                "take_profit": self.config.strategy.take_profit,
                "slippage": self.config.strategy.slippage,
                "buy_window_minutes": self.config.strategy.buy_window_minutes,
                "force_close_minutes": self.config.strategy.force_close_minutes,
                "rounds_per_market": self.config.strategy.rounds_per_market,
                "buy_amount": self.config.strategy.buy_amount,
            },
            "credentials": {
                "private_key": self.config.credentials.private_key,
                "api_key": self.config.credentials.api_key,
                "api_secret": self.config.credentials.api_secret,
                "api_passphrase": self.config.credentials.api_passphrase,
                "funder_address": self.config.credentials.funder_address,
            }
        }
        tmp_path = self.config_path + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, self.config_path)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add server/config.py tests/test_config.py
git commit -m "feat: add configuration management"
```

---

## Task 3: 凭据管理 (credentials.py)

**Files:**
- Create: `server/credentials.py`
- Create: `tests/test_credentials.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_credentials.py
import pytest
from server.credentials import CredentialsManager

def test_credentials_from_env(monkeypatch):
    monkeypatch.setenv("POLY_PRIVATE_KEY", "0x123")
    monkeypatch.setenv("POLY_API_KEY", "key123")
    cm = CredentialsManager()
    assert cm.private_key == "0x123"
    assert cm.api_key == "key123"

def test_credentials_from_config():
    cm = CredentialsManager()
    cm.config.credentials.private_key = "0xabc"
    cm.config.credentials.api_key = "abc_key"
    assert cm.private_key == "0xabc"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_credentials.py -v`
Expected: FAIL

- [ ] **Step 3: Write credentials.py**

```python
"""Credentials management - loads from env vars or config."""
import os
from server.config import ConfigManager


class CredentialsManager:
    """Manages API credentials from environment or config."""

    def __init__(self):
        self.config = ConfigManager()

    @property
    def private_key(self) -> str:
        return os.getenv("POLY_PRIVATE_KEY") or self.config.credentials.private_key

    @property
    def api_key(self) -> str:
        return os.getenv("POLY_API_KEY") or self.config.credentials.api_key

    @property
    def api_secret(self) -> str:
        return os.getenv("POLY_API_SECRET") or self.config.credentials.api_secret

    @property
    def api_passphrase(self) -> str:
        return os.getenv("POLY_API_PASSPHRASE") or self.config.credentials.api_passphrase

    @property
    def funder_address(self) -> str:
        return os.getenv("POLY_FUNDER_ADDRESS") or self.config.credentials.funder_address
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_credentials.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add server/credentials.py tests/test_credentials.py
git commit -m "feat: add credentials management"
```

---

## Task 4: 市场信息管理 (market_info.py)

**Files:**
- Create: `server/market_info.py`
- Create: `tests/test_market_info.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_market_info.py
import pytest
import time
from server.market_info import MarketInfoManager, get_current_slug, get_next_slug

def test_get_current_slug_format():
    slug = get_current_slug()
    assert slug.startswith("btc-updown-5m-")
    parts = slug.split("-")
    timestamp = int(parts[-1])
    assert timestamp > time.time()
    assert (timestamp - int(time.time())) % 300 in (0, 300 - (int(time.time()) % 300))

def test_get_next_slug():
    current = get_current_slug()
    next_slug = get_next_slug()
    assert next_slug != current
    current_ts = int(current.split("-")[-1])
    next_ts = int(next_slug.split("-")[-1])
    assert next_ts > current_ts

@pytest.mark.asyncio
async def test_fetch_market_info():
    manager = MarketInfoManager()
    slug = get_current_slug()
    info = await manager.get_market_info(slug)
    assert info is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_market_info.py -v`
Expected: FAIL

- [ ] **Step 3: Write market_info.py**

```python
"""Market information and slug management."""
import time
import httpx
from typing import Optional, Dict, Any

GAMMA_API = "https://gamma-api.polymarket.com"


def get_current_slug() -> str:
    """Get the current market slug based on current time."""
    now = time.time()
    period = 300  # 5 minutes
    end_timestamp = int(now // period) * period + period
    return f"btc-updown-5m-{end_timestamp}"


def get_next_slug() -> str:
    """Get the next market slug."""
    now = time.time()
    period = 300
    next_end = int(now // period) * period + 600
    return f"btc-updown-5m-{next_end}"


def get_slug_end_timestamp(slug: str) -> int:
    """Extract end timestamp from slug."""
    return int(slug.split("-")[-1])


def get_slug_start_timestamp(slug: str) -> int:
    """Get market start timestamp (5 minutes before end)."""
    return get_slug_end_timestamp(slug) - 300


class MarketInfoManager:
    """Fetches and caches market information from Gamma API."""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_time: Dict[str, float] = {}
        self._cache_ttl = 60  # Cache for 60 seconds

    async def get_market_info(self, slug: str) -> Optional[Dict[str, Any]]:
        """Fetch market info from Gamma API."""
        if slug in self._cache:
            if time.time() - self._cache_time[slug] < self._cache_ttl:
                return self._cache[slug]

        url = f"{GAMMA_API}/markets/slug/{slug}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    self._cache[slug] = data
                    self._cache_time[slug] = time.time()
                    return data
            except Exception as e:
                print(f"Error fetching market info: {e}")
                return None

        return None

    async def get_token_ids(self, slug: str) -> Optional[tuple]:
        """Get YES and NO token IDs for a market."""
        info = await self.get_market_info(slug)
        if not info:
            return None

        clob_token_ids = info.get("clobTokenIds", "")
        if not clob_token_ids:
            return None

        tokens = clob_token_ids.split(",")
        if len(tokens) >= 2:
            return tokens[0], tokens[1]  # (yes_token, no_token)

        return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_market_info.py -v`
Expected: PASS (may need network)

- [ ] **Step 5: Commit**

```bash
git add server/market_info.py tests/test_market_info.py
git commit -m "feat: add market info and slug management"
```

---

## Task 5: 价格轮询器 (price_poller.py) — 核心新模块

**Files:**
- Create: `server/price_poller.py`
- Create: `tests/test_price_poller.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_price_poller.py
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from server.price_poller import PricePoller

@pytest.mark.asyncio
async def test_price_poller_init():
    poller = PricePoller("yes_token", "no_token", lambda y, n: None)
    assert poller.yes_token == "yes_token"
    assert poller.no_token == "no_token"
    assert poller.POLL_INTERVAL == 0.5

@pytest.mark.asyncio
async def test_calculate_prices():
    collected = []
    def callback(yes, no):
        collected.append((yes, no))

    poller = PricePoller("yes_token", "no_token", callback)

    mock_response = {
        "yes_token": {"BUY": 0.21},
        "no_token": {"SELL": 0.79}
    }

    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_response_obj = AsyncMock()
        mock_response_obj.status_code = 200
        mock_response_obj.json = AsyncMock(return_value=mock_response)
        mock_instance.post = AsyncMock(return_value=mock_response_obj)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

        await poller._fetch_prices()

    assert len(collected) == 1
    assert collected[0] == (0.21, 0.79)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_price_poller.py -v`
Expected: FAIL

- [ ] **Step 3: Write price_poller.py**

```python
"""REST API 价格轮询器，替代 WebSocket 获取价格。"""
import asyncio
import httpx
from typing import Callable, Tuple

CLOB_API = "https://clob.polymarket.com"


class PricePoller:
    """REST API 价格轮询器，每500ms获取一次价格。"""

    POLL_INTERVAL = 0.5  # 500ms

    def __init__(self, yes_token: str, no_token: str, price_callback: Callable[[float, float], None]):
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
                    yes_price = data.get(self.yes_token, {}).get("BUY", 0.0)
                    no_price = data.get(self.no_token, {}).get("SELL", 0.0)
                    self._yes_price = yes_price
                    self._no_price = no_price
                    self.price_callback(yes_price, no_price)
                else:
                    print(f"Price fetch failed: {resp.status_code}")
            except Exception as e:
                print(f"Price fetch error: {e}")

    @property
    def prices(self) -> Tuple[float, float]:
        """返回当前缓存的价格 (yes, no)。"""
        return (self._yes_price, self._no_price)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_price_poller.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add server/price_poller.py tests/test_price_poller.py
git commit -m "feat: add REST price poller (replaces WebSocket market_tracker)"
```

---

## Task 6: 订单服务 (order_service.py)

**Files:**
- Create: `server/order_service.py`
- Create: `tests/test_order_service.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_order_service.py
import pytest
from server.order_service import OrderService, OrderType, Position

def test_position_creation():
    pos = Position(
        direction="YES",
        buy_price=20.0,
        buy_order_id="0x123",
        amount=1.0
    )
    assert pos.direction == "YES"
    assert pos.buy_price == 20.0
    assert pos.status == "open"
    assert pos.sell_order_id is None

def test_calculate_buy_price_with_slippage():
    price = OrderService.calculate_buy_price(20.0, 0.10)
    assert price == 22.0  # 20 * (1 + 0.10)

def test_calculate_sell_price_with_slippage():
    price = OrderService.calculate_sell_price(20.0, 0.10)
    assert price == 18.0  # 20 * (1 - 0.10)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_order_service.py -v`
Expected: FAIL

- [ ] **Step 3: Write order_service.py**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_order_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add server/order_service.py tests/test_order_service.py
git commit -m "feat: add order service with FOK market orders"
```

---

## Task 7: 交易记录 (trade_log.py)

**Files:**
- Create: `server/trade_log.py`
- Create: `tests/test_trade_log.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_trade_log.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_trade_log.py -v`
Expected: FAIL

- [ ] **Step 3: Write trade_log.py**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_trade_log.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add server/trade_log.py tests/test_trade_log.py
git commit -m "feat: add trade logging service"
```

---

## Task 8: 自动交易状态机 (auto_trader.py)

**Files:**
- Create: `server/auto_trader.py`
- Create: `tests/test_auto_trader.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_auto_trader.py
import pytest
from server.auto_trader import AutoTrader, TraderState, MarketState

def test_trader_state_enum():
    assert TraderState.IDLE.value == "IDLE"
    assert TraderState.LISTENING.value == "LISTENING"
    assert TraderState.MONITORING.value == "MONITORING"
    assert TraderState.DONE.value == "DONE"

def test_auto_trader_init():
    from server.config import ConfigManager
    from server.market_info import MarketInfoManager
    from server.order_service import OrderService
    from server.trade_log import TradeLog
    from server.credentials import CredentialsManager

    config = ConfigManager()
    credentials = CredentialsManager()
    market_info = MarketInfoManager()
    order_service = OrderService(credentials)
    trade_log = TradeLog()

    trader = AutoTrader(config, market_info, order_service, trade_log)
    assert trader.state == TraderState.IDLE
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_auto_trader.py -v`
Expected: FAIL

- [ ] **Step 3: Write auto_trader.py**

```python
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

        self.state = TraderState.IDLE
        self.market = MarketState()
        self._running = False
        self._trade_count = 0

    def set_websocket_handler(self, ws_handler):
        self.ws_handler = ws_handler

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

        print(f"New market: {slug}, starts in {self.market.start_time - time.time():.0f}s")

    async def _enter_listening(self):
        self.state = TraderState.LISTENING
        self.market.current_round = 0
        print(f"Entering LISTENING state for {self.market.slug}")

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

        print(f"Buying {direction} at {buy_price} (price: {price}, slippage: {slippage})")

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

            print(f"Bought {direction} at {buy_price}, position created")

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

        print(f"Closing {position.direction} position at {sell_price} (reason: {reason})")

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

            print(f"Closed {position.direction} at {sell_price}, PnL: {pnl:.2f}")

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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_auto_trader.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add server/auto_trader.py tests/test_auto_trader.py
git commit -m "feat: add auto-trader state machine"
```

---

## Task 9: WebSocket处理器 (websocket_handler.py)

**Files:**
- Create: `server/websocket_handler.py`
- Create: `tests/test_websocket_handler.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_websocket_handler.py
import pytest
from server.websocket_handler import WSHandler

def test_ws_handler_init():
    handler = WSHandler(host="localhost", port=8766)
    assert handler.host == "localhost"
    assert handler.port == 8766
    assert not handler._running
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_websocket_handler.py -v`
Expected: FAIL

- [ ] **Step 3: Write websocket_handler.py**

```python
"""WebSocket handler for frontend communication."""
import asyncio
import json
import websockets
from typing import Set, Optional, Dict, Any


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
        print(f"WebSocket server started on ws://{self.host}:{self.port}")

    async def stop(self):
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        print("WebSocket server stopped")

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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_websocket_handler.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add server/websocket_handler.py tests/test_websocket_handler.py
git commit -m "feat: add WebSocket handler for frontend"
```

---

## Task 10: 主入口 (main.py)

**Files:**
- Create: `server/main.py`

- [ ] **Step 1: Write main.py**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add server/main.py
git commit -m "feat: add main entry point with price poller"
```

---

## Task 11: Chrome Extension 前端

**Files:**
- Create: `extension/manifest.json`
- Create: `extension/sidepanel/index.html`
- Create: `extension/sidepanel/app.js`
- Create: `extension/sidepanel/style.css`

- [ ] **Step 1: Create manifest.json**

```json
{
  "manifest_version": 3,
  "name": "Polymarket BTC 5m Auto Trader",
  "version": "1.0.0",
  "description": "Automated trading for BTC 5-minute up/down markets",
  "permissions": ["sidePanel"],
  "host_permissions": ["*://*.polymarket.com/*", "ws://localhost:8766/*"],
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },
  "side_panel": {
    "default_path": "sidepanel/index.html"
  }
}
```

- [ ] **Step 2: Create index.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BTC 5m Auto Trader</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Polymarket BTC 5m Auto Trader</h1>
        </header>

        <nav class="tabs">
            <button class="tab active" data-tab="market">Market</button>
            <button class="tab" data-tab="trades">Trades</button>
            <button class="tab" data-tab="config">Config</button>
        </nav>

        <main>
            <section id="market-tab" class="tab-content active">
                <div class="market-info">
                    <div class="market-slug" id="market-slug">Loading...</div>
                    <div class="status" id="status">IDLE</div>
                </div>

                <div class="prices">
                    <div class="price-card yes">
                        <span class="label">YES</span>
                        <span class="value" id="yes-price">--</span>
                    </div>
                    <div class="price-card no">
                        <span class="label">NO</span>
                        <span class="value" id="no-price">--</span>
                    </div>
                </div>

                <div class="timer">
                    <div>Time until start: <span id="time-start">--</span>s</div>
                    <div>Time until end: <span id="time-end">--</span>s</div>
                </div>

                <div class="positions" id="positions">
                    <h3>Positions</h3>
                    <div id="positions-list">No open positions</div>
                </div>

                <div class="controls">
                    <button id="btn-start">Start Trading</button>
                    <button id="btn-stop">Stop Trading</button>
                </div>
            </section>

            <section id="trades-tab" class="tab-content">
                <h3>Trade History</h3>
                <div id="trades-list" class="trades-list">
                    <p>No trades yet</p>
                </div>
            </section>

            <section id="config-tab" class="tab-content">
                <h3>Trading Configuration</h3>
                <form id="config-form">
                    <div class="form-group">
                        <label>Buy Price Min</label>
                        <input type="number" id="buy_price_min" value="18" step="0.1">
                    </div>
                    <div class="form-group">
                        <label>Buy Price Max</label>
                        <input type="number" id="buy_price_max" value="22" step="0.1">
                    </div>
                    <div class="form-group">
                        <label>Stop Loss</label>
                        <input type="number" id="stop_loss" value="13" step="0.1">
                    </div>
                    <div class="form-group">
                        <label>Take Profit</label>
                        <input type="number" id="take_profit" value="35" step="0.1">
                    </div>
                    <div class="form-group">
                        <label>Slippage (%)</label>
                        <input type="number" id="slippage" value="10" step="1">
                    </div>
                    <div class="form-group">
                        <label>Buy Window (minutes)</label>
                        <input type="number" id="buy_window_minutes" value="2" step="1">
                    </div>
                    <div class="form-group">
                        <label>Force Close (minutes)</label>
                        <input type="number" id="force_close_minutes" value="1" step="1">
                    </div>
                    <div class="form-group">
                        <label>Rounds per Market</label>
                        <input type="number" id="rounds_per_market" value="3" step="1">
                    </div>
                    <div class="form-group">
                        <label>Buy Amount (USD)</label>
                        <input type="number" id="buy_amount" value="1.0" step="0.1">
                    </div>
                    <button type="submit">Save Configuration</button>
                </form>
            </section>
        </main>
    </div>
    <script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 3: Create style.css**

```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #1a1a2e;
    color: #eee;
    min-width: 320px;
    padding: 16px;
}

.container {
    max-width: 400px;
    margin: 0 auto;
}

header h1 {
    font-size: 16px;
    text-align: center;
    margin-bottom: 16px;
    color: #00d4ff;
}

.tabs {
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
}

.tab {
    flex: 1;
    padding: 8px 16px;
    background: #2a2a4e;
    border: none;
    color: #aaa;
    cursor: pointer;
    border-radius: 4px;
}

.tab.active {
    background: #00d4ff;
    color: #1a1a2e;
}

.tab-content {
    display: none;
}

.tab-content.active {
    display: block;
}

.market-info {
    text-align: center;
    margin-bottom: 16px;
}

.market-slug {
    font-size: 12px;
    color: #888;
    word-break: break-all;
}

.status {
    font-size: 24px;
    font-weight: bold;
    margin: 8px 0;
    color: #00d4ff;
}

.prices {
    display: flex;
    gap: 16px;
    margin-bottom: 16px;
}

.price-card {
    flex: 1;
    padding: 16px;
    background: #2a2a4e;
    border-radius: 8px;
    text-align: center;
}

.price-card.yes {
    border-left: 3px solid #4caf50;
}

.price-card.no {
    border-left: 3px solid #f44336;
}

.price-card .label {
    display: block;
    font-size: 12px;
    color: #888;
    margin-bottom: 8px;
}

.price-card .value {
    font-size: 24px;
    font-weight: bold;
}

.timer {
    background: #2a2a4e;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 16px;
    font-size: 14px;
}

.timer div {
    margin: 4px 0;
}

.positions {
    background: #2a2a4e;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 16px;
}

.positions h3 {
    font-size: 14px;
    margin-bottom: 8px;
}

.position-item {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid #3a3a5e;
}

.position-item:last-child {
    border-bottom: none;
}

.position-item.yes {
    color: #4caf50;
}

.position-item.no {
    color: #f44336;
}

.pnl {
    font-weight: bold;
}

.pnl.positive {
    color: #4caf50;
}

.pnl.negative {
    color: #f44336;
}

.controls {
    display: flex;
    gap: 8px;
}

button {
    flex: 1;
    padding: 12px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: bold;
}

#btn-start {
    background: #4caf50;
    color: white;
}

#btn-stop {
    background: #f44336;
    color: white;
}

.trades-list {
    max-height: 300px;
    overflow-y: auto;
}

.trade-item {
    background: #2a2a4e;
    padding: 12px;
    border-radius: 4px;
    margin-bottom: 8px;
}

.trade-item .header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 4px;
}

.trade-item .side {
    font-weight: bold;
}

.trade-item .side.buy {
    color: #4caf50;
}

.trade-item .side.sell {
    color: #f44336;
}

.trade-item .exit-reason {
    font-size: 12px;
    color: #888;
}

.form-group {
    margin-bottom: 12px;
}

.form-group label {
    display: block;
    font-size: 12px;
    color: #888;
    margin-bottom: 4px;
}

.form-group input {
    width: 100%;
    padding: 8px;
    background: #2a2a4e;
    border: 1px solid #3a3a5e;
    border-radius: 4px;
    color: #eee;
}

form button {
    width: 100%;
    background: #00d4ff;
    color: #1a1a2e;
    margin-top: 8px;
}
```

- [ ] **Step 4: Create app.js**

```javascript
class TradingApp {
    constructor() {
        this.ws = null;
        this.connected = false;
        this.state = 'IDLE';
        this.prices = { YES: 0, NO: 0 };
        this.positions = [];
        this.trades = [];

        this.initTabs();
        this.initWebSocket();
        this.initControls();
        this.initConfigForm();
    }

    initTabs() {
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                tab.classList.add('active');
                document.getElementById(`${tab.dataset.tab}-tab`).classList.add('active');
            });
        });
    }

    initWebSocket() {
        this.connect();
        setInterval(() => {
            if (!this.connected) {
                this.connect();
            }
        }, 5000);
    }

    connect() {
        try {
            this.ws = new WebSocket('ws://localhost:8766');

            this.ws.onopen = () => {
                console.log('Connected to server');
                this.connected = true;
                this.requestStatus();
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            };

            this.ws.onclose = () => {
                console.log('Disconnected from server');
                this.connected = false;
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.connected = false;
            };
        } catch (error) {
            console.error('Connection failed:', error);
        }
    }

    handleMessage(data) {
        switch (data.type) {
            case 'status':
                this.updateStatus(data.data);
                break;
            case 'market_update':
                this.updateMarket(data.data);
                break;
            case 'trade_update':
                this.addTrade(data.data);
                break;
            case 'config':
                this.loadConfig(data.data);
                break;
        }
    }

    updateStatus(status) {
        this.state = status.state;
        document.getElementById('status').textContent = status.state;
        document.getElementById('market-slug').textContent = status.slug || 'Loading...';

        if (status.yes_price) {
            this.prices.YES = status.yes_price;
            document.getElementById('yes-price').textContent = status.yes_price.toFixed(2);
        }

        if (status.no_price) {
            this.prices.NO = status.no_price;
            document.getElementById('no-price').textContent = status.no_price.toFixed(2);
        }

        this.updatePositions(status.positions || []);
    }

    updateMarket(data) {
        if (data.yes_price) {
            this.prices.YES = data.yes_price;
            document.getElementById('yes-price').textContent = data.yes_price.toFixed(2);
        }

        if (data.no_price) {
            this.prices.NO = data.no_price;
            document.getElementById('no-price').textContent = data.no_price.toFixed(2);
        }

        if (data.time_until_start !== undefined) {
            document.getElementById('time-start').textContent = Math.max(0, data.time_until_start).toFixed(0);
        }

        if (data.time_until_end !== undefined) {
            document.getElementById('time-end').textContent = Math.max(0, data.time_until_end).toFixed(0);
        }

        if (data.state) {
            this.state = data.state;
            document.getElementById('status').textContent = data.state;
        }
    }

    updatePositions(positions) {
        this.positions = positions;
        const list = document.getElementById('positions-list');

        if (positions.length === 0) {
            list.innerHTML = '<p>No open positions</p>';
            return;
        }

        list.innerHTML = positions.map(p => {
            const pnl = p.pnl || 0;
            const pnlClass = pnl >= 0 ? 'positive' : 'negative';
            return `
                <div class="position-item ${p.direction.toLowerCase()}">
                    <span>${p.direction} @ ${p.buy_price.toFixed(2)}</span>
                    <span class="pnl ${pnlClass}">${pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}</span>
                </div>
            `;
        }).join('');
    }

    addTrade(trade) {
        this.trades.unshift(trade);
        this.renderTrades();
    }

    renderTrades() {
        const list = document.getElementById('trades-list');

        if (this.trades.length === 0) {
            list.innerHTML = '<p>No trades yet</p>';
            return;
        }

        list.innerHTML = this.trades.map(t => {
            const sideClass = t.side.toLowerCase();
            return `
                <div class="trade-item">
                    <div class="header">
                        <span class="side ${sideClass}">${t.side} ${t.direction}</span>
                        <span>${new Date(t.timestamp * 1000).toLocaleTimeString()}</span>
                    </div>
                    <div>Price: ${t.price.toFixed(2)} | Amount: $${t.amount}</div>
                    ${t.exit_reason ? `<div class="exit-reason">Exit: ${t.exit_reason} | PnL: ${(t.pnl || 0).toFixed(2)}</div>` : ''}
                </div>
            `;
        }).join('');
    }

    loadConfig(config) {
        if (config.strategy) {
            Object.entries(config.strategy).forEach(([key, value]) => {
                const input = document.getElementById(key);
                if (input) input.value = value;
            });
        }
    }

    initControls() {
        document.getElementById('btn-start').addEventListener('click', () => {
            this.send({ type: 'start' });
        });

        document.getElementById('btn-stop').addEventListener('click', () => {
            this.send({ type: 'stop' });
        });
    }

    initConfigForm() {
        document.getElementById('config-form').addEventListener('submit', (e) => {
            e.preventDefault();
            const strategy = {};
            ['buy_price_min', 'buy_price_max', 'stop_loss', 'take_profit',
             'slippage', 'buy_window_minutes', 'force_close_minutes',
             'rounds_per_market', 'buy_amount'].forEach(key => {
                const input = document.getElementById(key);
                if (input) {
                    strategy[key] = parseFloat(input.value);
                }
            });
            this.send({ type: 'update_config', data: { strategy } });
        });
    }

    requestStatus() {
        this.send({ type: 'get_status' });
    }

    send(data) {
        if (this.ws && this.connected) {
            this.ws.send(JSON.stringify(data));
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.app = new TradingApp();
});
```

- [ ] **Step 5: Commit**

```bash
git add extension/manifest.json extension/sidepanel/
git commit -m "feat: add Chrome Extension frontend"
```

---

## Task 12: 集成测试

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test skeleton**

```python
# tests/test_integration.py
import pytest

def test_integration_imports():
    """Verify all modules can be imported."""
    from server.config import ConfigManager
    from server.credentials import CredentialsManager
    from server.market_info import MarketInfoManager
    from server.price_poller import PricePoller
    from server.order_service import OrderService
    from server.trade_log import TradeLog
    from server.auto_trader import AutoTrader
    from server.websocket_handler import WSHandler
    assert True
```

- [ ] **Step 2: Run integration test**

Run: `pytest tests/test_integration.py -v`

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration test"
```

---

## 实施总结

| Task | 文件 | 描述 |
|------|------|------|
| 1 | requirements.txt, config.json | 项目初始化 |
| 2 | config.py | 配置管理 |
| 3 | credentials.py | 凭据加载 |
| 4 | market_info.py | 市场slug和信息 |
| 5 | **price_poller.py** | **REST API 价格轮询 (新增，替代market_tracker)** |
| 6 | order_service.py | 订单服务 |
| 7 | trade_log.py | 交易记录 |
| 8 | auto_trader.py | 交易状态机 |
| 9 | websocket_handler.py | 前端通信 |
| 10 | main.py | 主入口 |
| 11 | extension/* | Chrome扩展前端 |
| 12 | tests/* | 集成测试 |

---

**Plan complete and saved to `docs/superpowers/plans/2026-04-02-polymarket-btc5m-auto-trade-plan-v2.md`**

Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
