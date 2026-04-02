# Polymarket BTC 5分钟涨跌自动交易系统设计

**日期：** 2026-04-02
**项目：** pm-auto-trade2.0
**状态：** 设计完成

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
│  │ MarketTracker │  │ AutoTrader   │  │ OrderService  │     │
│  │ (WebSocket)  │  │ (状态机)     │  │ (下单/重试)   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ ConfigManager│  │ TradeLog     │  │ WSHandler    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Polymarket CLOB API                      │
│  WebSocket: wss://ws-subscriptions-clob.polymarket.com     │
│  REST API:   https://clob.polymarket.com                   │
└─────────────────────────────────────────────────────────────┘
```

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
│   ├── client.py               # CLOB客户端初始化
│   ├── market_info.py          # slug解析、tokenID获取
│   ├── market_tracker.py       # Polymarket WebSocket管理
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
            └── 2026-04-02-polymarket-btc5m-auto-trade-design.md
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

**当前市场 slug 示例：** `btc-updown-5m-1774273500`

**Slug 计算逻辑：**
```python
def get_current_slug() -> str:
    now = time.time()
    # 5分钟市场 = 300秒
    period = 300
    # 市场结束时间 = 向下取整(now / 300) * 300 + 300
    end_timestamp = int(now // period) * period + period
    return f"btc-updown-5m-{end_timestamp}"

def get_next_slug() -> str:
    now = time.time()
    period = 300
    next_end = int(now // period) * period + 600  # 下一个市场
    return f"btc-updown-5m-{next_end}"
```

**自动切换：** 当 `now >= market_end_time` 时，切换到下一个 slug。

---

## 6. AutoTrader 状态机

```
                    ┌──────────────┐
                    │    IDLE     │ (等待市场开始)
                    └──────┬──────┘
                           │ 市场开始前2分钟
                           ▼
                 ┌─────────────────────┐
        ┌─────── │     LISTENING        │◄─────────────┐
        │        │ - 监控YES/NO价格     │              │
        │        │ - 符合条件立即买入   │              │
        │        │ - 买入后立即启动止盈止损监测              │
        │        └─────────┬───────────┘              │
        │                  │ 买入窗口关闭/rounds满     │
        │                  ▼                          │
        │        ┌─────────────────────┐              │
        │        │     MONITORING     │              │
        │        │ - 监控所有持仓     │              │
        │        │ - 止盈/止损/强制平仓│              │
        │        └─────────┬───────────┘              │
        │                  │ 所有仓位平仓             │
        │                  ▼                          │
        │        ┌─────────────────────┐              │
        │        │       DONE         │──────────────┘
        │        │ (切换下一个市场)    │ (rounds < max)
        │        └─────────────────────┘
        │                  │
        │                  │ 市场结束
        │                  ▼
        └──────── 切换到下一个slug
```

**说明：**
- LISTENING 状态中：每个仓位独立监测止盈止损
- 买入窗口内可以继续买入（最多 `rounds_per_market` 轮）
- 每个仓位独立的止盈止损监测，互不干扰

---

## 7. 交易逻辑

### 7.1 买入逻辑

| 条件 | 价格触发 |
|------|----------|
| YES 价格 ∈ [18, 22] | 买入 YES |
| NO 价格 ∈ [18, 22] | 买入 NO |

**市价单买入流程：**
1. 获取当前价格
2. 计算买入价格 = 当前价格 × (1 + slippage)
3. 使用 FOK 订单类型（市价单，立即成交）
4. 超时时间：5秒
5. 失败重试：最多3次，间隔2秒

### 7.2 止盈止损

**买入成功后立即启动**，针对每个仓位独立监测：

| 条件 | 动作 |
|------|------|
| 当前价格 ≥ 35 | 市价卖出（止盈） |
| 当前价格 ≤ 13 | 市价卖出（止损） |
| 距离市场结束 ≤ 1分钟 | 市价卖出（强制平仓） |

### 7.3 卖出逻辑

**市价单卖出流程：**
1. 获取当前价格
2. 计算卖出价格 = 当前价格 × (1 - slippage)
3. 使用 FOK 订单类型
4. 超时时间：5秒
5. 失败重试：最多3次，间隔2秒

---

## 8. Polymarket WebSocket 连接管理

**端点：** `wss://ws-subscriptions-clob.polymarket.com/ws/market`

### 8.1 连接流程

```
连接建立
    ↓
发送订阅消息（包含 asset_ids）
    ↓
进入主循环（50ms价格检测）
    ↓
每10秒发送 PING 心跳
```

### 8.2 断线重连

| 状态 | 说明 |
|------|------|
| `CONNECTED` | 正常运行 |
| `RECONNECTING` | 断线重连中 |
| `DISCONNECTED` | 已断开 |

**重连策略：指数退避**
```
1s → 2s → 4s → 8s → 16s → 32s → 60s（最大）
```

**重连触发条件：**
- 发送 PING 后 30 秒无 PONG 响应
- WebSocket 连接错误
- 服务器主动关闭连接

**重连恢复：**
1. 重新建立 WebSocket 连接
2. 重新订阅市场
3. 恢复价格检测

---

## 9. 订单可靠性

### 9.1 Nonce 管理

```python
class NonceManager:
    _lock: asyncio.Lock
    _nonce: int

    async def get_next_nonce(self) -> int:
        async with self._lock:
            self._nonce += 1
            return self._nonce
```

### 9.2 仓位追踪

```python
class Position:
    direction: str           # "YES" or "NO"
    buy_price: float
    buy_order_id: str
    amount: float
    sell_order_id: str | None
    status: str              # "open", "sold", "closed"
    created_at: float
```

### 9.3 订单类型

| 订单类型 | 使用场景 |
|----------|----------|
| FOK (Fill or Kill) | 市价单，5秒内未成交则失败 |

---

## 10. WebSocket 消息格式

### 10.1 服务器 → 前端

**市场信息更新：**
```json
{
  "type": "market_update",
  "data": {
    "slug": "btc-updown-5m-1774273500",
    "yes_price": 21.5,
    "no_price": 78.5,
    "time_until_start": 120,
    "time_until_end": 180,
    "state": "LISTENING"
  }
}
```

**交易记录更新：**
```json
{
  "type": "trade_update",
  "data": {
    "round": 1,
    "side": "BUY",
    "direction": "YES",
    "price": 20.0,
    "amount": 1.0,
    "status": "filled",
    "timestamp": 1774273512,
    "pnl": null
  }
}
```

**持仓更新：**
```json
{
  "type": "position_update",
  "data": {
    "positions": [
      {
        "direction": "YES",
        "buy_price": 20.0,
        "current_price": 25.0,
        "pnl": 0.25,
        "stop_loss": 13,
        "take_profit": 35
      }
    ]
  }
}
```

### 10.2 前端 → 服务器

**更新配置：**
```json
{
  "type": "update_config",
  "data": {
    "buy_price_min": 18,
    "buy_price_max": 22
  }
}
```

**获取配置：**
```json
{
  "type": "get_config",
  "data": {}
}
```

---

## 11. 数据持久化

### 11.1 配置持久化

**文件：** `data/config.json`

**原子写入：**
```python
def save_config(config):
    with open("config.json.tmp", "w") as f:
        json.dump(config, f, indent=2)
    os.rename("config.json.tmp", "config.json")
```

### 11.2 交易记录

**文件：** `data/trades/trades-{date}.json`

```json
{
  "date": "2026-04-02",
  "trades": [
    {
      "timestamp": 1774273512,
      "market_slug": "btc-updown-5m-1774273500",
      "round": 1,
      "side": "BUY",
      "direction": "YES",
      "price": 20.0,
      "amount": 1.0,
      "order_id": "0xabc...",
      "status": "filled"
    },
    {
      "timestamp": 1774273530,
      "side": "SELL",
      "direction": "YES",
      "price": 35.0,
      "amount": 1.0,
      "order_id": "0xdef...",
      "status": "filled",
      "exit_reason": "take_profit",
      "pnl": 0.75
    }
  ]
}
```

### 11.3 状态快照

**保存频率：** 每30秒
**用途：** 异常退出后恢复

```json
{
  "timestamp": 1774273600,
  "current_slug": "btc-updown-5m-1774273500",
  "positions": [...],
  "nonce": 42
}
```

---

## 12. 性能优化

### 12.1 交易主循环

```python
class TradingLoop:
    PRICE_CHECK_INTERVAL = 0.05  # 50ms

    async def run(self):
        while True:
            # 价格检测（核心交易逻辑）
            await self.check_prices()

            # 止盈止损检测（同一循环内）
            await self.check_exit_conditions()

            # 稳定性任务（异步，不阻塞）
            asyncio.create_task(self.maybe_flush_logs())
            asyncio.create_task(self.maybe_save_snapshot())

            await asyncio.sleep(self.PRICE_CHECK_INTERVAL)
```

### 12.2 预热机制

市场开始前2分钟：
1. 建立 Polymarket WebSocket 连接
2. 获取当前市场 tokenId、conditionId
3. 预计算下一个市场 slug
4. 启动 50ms 高频价格检测循环

---

## 13. 错误处理

| 错误类型 | 处理方式 |
|----------|----------|
| 网络断线 | 自动重连，暂停交易 |
| API 限流 (429) | 等待指定时间后重试 |
| Nonce 冲突 | 递增 nonce 重试 |
| 余额不足 | 记录日志，跳过交易 |
| 市场关闭 | 取消挂单，切换市场 |
| 订单超时 | 重试最多3次 |

---

## 14. Chrome Extension 前端

### 14.1 界面布局

```
┌────────────────────────────────────────┐
│  Polymarket BTC 5m 自动交易            │
├────────────────────────────────────────┤
│  [市场信息]  [交易记录]  [配置]         │
├────────────────────────────────────────┤
│                                        │
│  市场：btc-updown-5m-1774273500        │
│  状态：LISTENING                       │
│                                        │
│  YES: 21.5  ▲                         │
│  NO:  78.5  ▼                         │
│                                        │
│  距离开始：120秒                        │
│  距离结束：180秒                        │
│                                        │
│  当前持仓：                             │
│  - YES @ 20.0 (盈 +0.25)              │
│                                        │
├────────────────────────────────────────┤
│  [开始交易]  [暂停交易]  [重置]         │
└────────────────────────────────────────┘
```

### 14.2 配置界面

```
┌────────────────────────────────────────┐
│  交易配置                              │
├────────────────────────────────────────┤
│  买入价格区间：                        │
│  [18] ～ [22]                          │
│                                        │
│  止损线：[13]                          │
│  止盈线：[35]                          │
│  滑点：  [10]%                         │
│                                        │
│  买入窗口：[2] 分钟                    │
│  强制平仓：[1] 分钟                    │
│  每市场轮数：[3]                       │
│  买入金额：[1.0] USD                  │
│                                        │
│  [保存配置]                            │
└────────────────────────────────────────┘
```

---

## 15. API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/order` | POST | 下单 |
| `/orders` | GET | 获取用户订单 |
| `/markets/slug/{slug}` | GET | 获取市场信息 |
| `/ws` | WebSocket | 服务器与前端通信 |

---

## 16. 相关文档

- Polymarket CLOB API: `https://clob.polymarket.com`
- Polymarket Gamma API: `https://gamma-api.polymarket.com`
- WebSocket: `wss://ws-subscriptions-clob.polymarket.com/ws/market`

---

**设计完成，待实现。**
