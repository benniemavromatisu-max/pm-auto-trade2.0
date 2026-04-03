# PM Auto Trade 2.0

Polymarket 自动交易机器人。

## 项目结构

```
pm-auto-trade2.0/
├── server/                    # Python 后端
│   ├── main.py              # 主入口，启动交易服务器
│   ├── auto_trader.py       # 自动交易状态机 (IDLE→LISTENING→MONITORING→DONE)
│   ├── order_service.py     # 订单服务 (下单、重试、token 份额查询)
│   ├── price_poller.py      # 价格轮询器 (REST API 500ms 轮询)
│   ├── websocket_handler.py  # WebSocket 处理器 (前端通信)
│   ├── market_info.py       # 市场信息管理
│   ├── config.py            # 配置管理
│   ├── credentials.py        # 凭证管理 (L1/L2 认证)
│   ├── trade_log.py         # 交易日志
│   └── server_logger.py      # 日志模块
├── extension/sidepanel/     # Chrome 扩展前端
│   ├── app.js              # 主应用逻辑
│   ├── index.html           # HTML
│   └── style.css            # 样式
└── data/                    # 运行时数据
    ├── config.json         # 配置文件
    ├── logs/                # 日志文件
    └── trades/             # 交易记录
```

## 交易策略

| 参数 | 默认值 | 说明 |
|------|--------|------|
| buy_price_min | 0.58 | 买入价格下限 |
| buy_price_max | 0.63 | 买入价格上限 |
| stop_loss | 0.50 | 止损价格 |
| take_profit | 0.67 | 止盈价格 |
| slippage | 0.10 | 滑点 10% |
| buy_window_minutes | 2 | 市场开始前 2 分钟开始检测 |
| force_close_minutes | 1 | 市场结束前 1 分钟强平 |
| rounds_per_market | 1 | 每个市场最多交易 1 轮 |

## 状态机

```
IDLE → LISTENING → MONITORING → DONE → IDLE

- IDLE: 等待市场开始前 buy_window 分钟
- LISTENING: 检测价格是否在 buy_price_min ~ buy_price_max
- MONITORING: 持有仓位，监控止盈/止损/强平
- DONE: 市场结束，重置
```

## 核心模块

### PricePoller
- 每 500ms 通过 REST API 获取价格
- 回调通知 AutoTrader
- 广播到前端

### AutoTrader
- 管理交易状态机
- 根据价格决定买入/卖出
- 调用 OrderService 执行

### OrderService
- 执行实际下单
- 获取 token 份额
- 重试机制

## 启动

```bash
python -m server.main
```

## 配置

编辑 `data/config.json` 修改交易参数。

## 技术栈

- Python 3.11 + asyncio
- httpx (HTTP 客户端)
- py-clob-client (Polymarket API)
- websockets (WebSocket 服务器)
- Chrome Extension (前端)
