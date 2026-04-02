# Polymarket BTC 5分钟涨跌自动交易系统设计 v2

**日期：** 2026-04-02
**版本：** v2（基于 v1 重新设计）
**变更：** 价格获取方式从 WebSocket 改为 REST API 轮询

---

## 1. 项目概述

**目标：** 构建一个 Polymarket BTC 5分钟涨跌市场的自动交易脚本，支持双向交易（YES/NO），具备止盈止损和强制平仓功能。

**核心功能：**
- 签名类型：POLY_PROXY (signatureType=1)
- 交易方向：YES（涨）和 NO（跌）
- 买入条件：价格进入 18~22 区间
- 止盈止损：买入后立即启动监测
- 强制平仓：最后1分钟
- 轮次控制：每个市场可交易多轮

---

## 2. 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Chrome Extension Side Panel               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  市场信息    │  │  交易记录    │  │   配置       │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                            │ WebSocket (ws://localhost:8766)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Python Async Server                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ PricePoller  │  │ AutoTrader   │  │ OrderService  │     │
│  │ (REST轮询)   │  │ (状态机)     │  │ (下单/重试)   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ ConfigManager│  │ TradeLog     │  │ WSHandler    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Polymarket CLOB API                       │
│  REST API:   https://clob.polymarket.com (POST /prices)    │
│  REST API:   https://gamma-api.polymarket.com (市场信息)    │
└─────────────────────────────────────────────────────────────┘
```

**关键变更：** 移除 Polymarket WebSocket 连接，改用 REST API 轮询获取价格。

---

## 3. 目录结构

```
pm-auto-trade2.0/
├── extension/                  # Chrome Extension
│   ├── manifest.json
│   ├── icons/
│   │   ├── icon16.png
│   │   ├── icon48.png
│   │   └── icon128.png
│   └── sidepanel/
│       ├── index.html          # 交易面板主页面
│       ├── app.js              # WebSocket客户端 + UI逻辑
│       └── style.css
├── server/                     # Python异步服务器
│   ├── main.py                 # 入口，启动所有任务
│   ├── config.py               # 配置管理
│   ├── credentials.py           # 私钥/API凭据管理
│   ├── market_info.py          # slug解析、tokenID获取
│   ├── price_poller.py         # REST API 价格轮询 (新增/重写)
│   ├── auto_trader.py         # 交易状态机
│   ├── order_service.py       # 订单操作
│   ├── trade_log.py           # 交易记录
│   ├── websocket_handler.py   # 与前端通信
│   └── requirements.txt
├── data/
│   ├── config.json            # 运行时配置
│   └── trades/
│       └── trades-{date}.json # 每日交易记录
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-04-02-polymarket-btc5m-auto-trade-design-v2.md
```

---

## 4. 配置参数

**文件：** `data/config.json`

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

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `buy_price_min` | 18 | 买入价格区间下限 |
| `buy_price_max` | 22 | 买入价格区间上限 |
| `stop_loss` | 13 | 止损线（跌破此价格卖出） |
| `take_profit` | 35 | 止盈线（涨到此价格卖出） |
| `slippage` | 0.10 | 滑点（买入加价10%，卖出减价10%） |
| `buy_window_minutes` | 2 | 市场开始前多少分钟允许买入 |
| `force_close_minutes` | 1 | 最后多少分钟强制平仓 |
| `rounds_per_market` | 3 | 每个市场最多几轮交易 |
| `buy_amount` | 1.0 | 每次买入金额（美元） |

---

## 5. 市场 Slug 管理

**格式：** `btc-updown-5m-{end_timestamp}`

**Slug 计算逻辑：**
```python
def get_current_slug() -> str:
    now = time.time()
    period = 300  # 5分钟 = 300秒
    end_timestamp = int(now // period) * period + period
    return f"btc-updown-5m-{end_timestamp}"
```

---

## 6. PricePoller（核心变更）

### 6.1 价格获取方式

**API：** `POST https://clob.polymarket.com/prices`

**请求体：**
```json
[
  { "token_id": "0xabc123...", "side": "BUY" },
  { "token_id": "0xdef456...", "side": "SELL" }
]
```

**响应：**
```json
{
  "0xabc123...": { "BUY": 0.21 },
  "0xdef456...": { "SELL": 0.79 }
}
```

### 6.2 轮询间隔

- **固定 500ms** 轮询间隔
- 使用 `asyncio.sleep` 精确控制

### 6.3 PricePoller 实现

```python
class PricePoller:
    """REST API 价格轮询器，替代 WebSocket 连接"""

    POLL_INTERVAL = 0.5  # 500ms
    CLOB_API = "https://clob.polymarket.com"

    def __init__(self, yes_token: str, no_token: str, price_callback: Callable):
        self.yes_token = yes_token
        self.no_token = no_token
        self.price_callback = price_callback  # 回调: (yes_price, no_price) -> None
        self._running = False

    async def start(self):
        """启动轮询循环"""
        self._running = True
        while self._running:
            await self._fetch_prices()
            await asyncio.sleep(self.POLL_INTERVAL)

    async def stop(self):
        """停止轮询"""
        self._running = False

    async def _fetch_prices(self):
        """从 REST API 获取价格"""
        payload = [
            { "token_id": self.yes_token, "side": "BUY" },
            { "token_id": self.no_token, "side": "SELL" }
        ]
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"{self.CLOB_API}/prices",
                    json=payload,
                    timeout=5.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    yes_price = data.get(self.yes_token, {}).get("BUY", 0)
                    no_price = data.get(self.no_token, {}).get("SELL", 0)
                    self.price_callback(yes_price, no_price)
            except Exception as e:
                print(f"Price fetch error: {e}")
```

### 6.4 与 AutoTrader 的集成

```python
# main.py
poller = PricePoller(
    yes_token=yes_token,
    no_token=no_token,
    price_callback=lambda yes_p, no_p: auto_trader.update_prices(yes_p, no_p)
)
await poller.start()
```

---

## 7. AutoTrader 状态机

**不变**，与 v1 设计一致。

```
IDLE → LISTENING → MONITORING → DONE
                          ↓
                    (切换下一市场)
```

---

## 8. 交易逻辑

**不变**，与 v1 设计一致。

### 8.1 买入逻辑
- YES/NO 价格在 [18, 22] 区间时买入
- 市价单 + 滑点

### 8.2 止盈止损
- 买入后立即针对每个仓位独立监测
- 涨至 35 → 止盈
- 跌至 13 → 止损
- 最后1分钟 → 强制平仓

---

## 9. 订单可靠性

**不变**，与 v1 设计一致。

- Nonce 管理
- 仓位追踪
- FOK 订单类型

---

## 10. WebSocket 消息格式

**不变**，与 v1 设计一致。

| 消息类型 | 方向 | 说明 |
|----------|------|------|
| `market_update` | 服务器→前端 | 价格/状态更新 |
| `trade_update` | 服务器→前端 | 交易记录 |
| `position_update` | 服务器→前端 | 持仓更新 |
| `update_config` | 前端→服务器 | 更新配置 |
| `get_config` | 前端→服务器 | 获取配置 |

---

## 11. 数据持久化

**不变**，与 v1 设计一致。

- 配置：`data/config.json`
- 交易记录：`data/trades/trades-{date}.json`
- 状态快照：每30秒

---

## 12. 错误处理

| 错误类型 | 处理方式 |
|----------|----------|
| API 请求失败 | 记录日志，继续下一次轮询 |
| 网络断线 | 继续轮询，价格保持不变 |
| 限流 (429) | 等待后重试 |
| 余额不足 | 记录日志，跳过交易 |
| 市场关闭 | 停止轮询，切换市场 |

---

## 13. Chrome Extension 前端

**不变**，与 v1 设计一致。

---

## 14. 性能优化

### 14.1 轮询循环

```python
async def run(self):
    while self._running:
        await self._fetch_prices()
        await asyncio.sleep(self.POLL_INTERVAL)  # 500ms
```

### 14.2 预热机制

市场开始前2分钟：
1. 获取当前市场 tokenId
2. 启动 500ms 价格轮询
3. 启动止盈止损监测

---

## 15. 变更总结

| 项目 | v1 (WebSocket) | v2 (REST轮询) |
|------|----------------|---------------|
| 价格获取 | WebSocket `wss://ws-subscriptions-clob.polymarket.com` | REST `POST /prices` |
| 更新频率 | 50ms | 500ms |
| 连接管理 | 复杂（心跳、重连） | 简单（无连接） |
| 断线处理 | 指数退避重连 | 自动重试 |
| API 依赖 | ws + rest | 仅 REST |

---

## 16. 相关文档

- Polymarket CLOB API: `https://clob.polymarket.com`
- Polymarket Gamma API: `https://gamma-api.polymarket.com`
- 价格 API: `POST /prices` (get-market-prices-request-body.md)

---

**设计完成，待实现。**
