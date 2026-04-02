> ## Documentation Index
> Fetch the complete documentation index at: https://docs.polymarket.com/llms.txt
> Use this file to discover all available pages before exploring further.

# User Channel

> 经过身份验证的订单和交易更新

这是一个经过身份验证的频道，用于接收与你的订单和交易相关的更新，按 API 密钥进行过滤。

## 端点

```
wss://ws-subscriptions-clob.polymarket.com/ws/user
```

## 身份验证

在订阅消息中包含 API 凭证:

```json  theme={null}
{
  "auth": {
    "apiKey": "your-api-key",
    "secret": "your-api-secret",
    "passphrase": "your-passphrase"
  },
  "markets": ["0x1234...condition_id"],
  "type": "user"
}
```

<Warning>
  永远不要在客户端代码中暴露你的 API 凭证。只在服务器环境中使用 user channel。
</Warning>

## 消息类型

每条消息都包含一个 `type` 字段来标识事件类型。

### trade

在以下情况下触发:

* 市价单被匹配 (`MATCHED`)
* 用户的限价单被包含在交易中 (`MATCHED`)
* 交易的后续状态变化 (`MINED`、`CONFIRMED`、`RETRYING`、`FAILED`)

```json  theme={null}
{
  "asset_id": "52114319501245915516055106046884209969926127482827954674443846427813813222426",
  "event_type": "trade",
  "id": "28c4d2eb-bbea-40e7-a9f0-b2fdb56b2c2e",
  "last_update": "1672290701",
  "maker_orders": [
    {
      "asset_id": "52114319501245915516055106046884209969926127482827954674443846427813813222426",
      "matched_amount": "10",
      "order_id": "0xff354cd7ca7539dfa9c28d90943ab5779a4eac34b9b37a757d7b32bdfb11790b",
      "outcome": "YES",
      "owner": "9180014b-33c8-9240-a14b-bdca11c0a465",
      "price": "0.57"
    }
  ],
  "market": "0xbd31dc8a20211944f6b70f31557f1001557b59905b7738480ca09bd4532f84af",
  "matchtime": "1672290701",
  "outcome": "YES",
  "owner": "9180014b-33c8-9240-a14b-bdca11c0a465",
  "price": "0.57",
  "side": "BUY",
  "size": "10",
  "status": "MATCHED",
  "taker_order_id": "0x06bc63e346ed4ceddce9efd6b3af37c8f8f440c92fe7da6b2d0f9e4ccbc50c42",
  "timestamp": "1672290701",
  "trade_owner": "9180014b-33c8-9240-a14b-bdca11c0a465",
  "type": "TRADE"
}
```

#### 交易状态

```
MATCHED → MINED → CONFIRMED
    ↓        ↑
RETRYING ───┘
    ↓
  FAILED
```

| 状态          | 是否终态 | 描述                          |
| ----------- | ---- | --------------------------- |
| `MATCHED`   | 否    | 交易已被匹配，并由运营商发送到执行服务         |
| `MINED`     | 否    | 交易已被观察到被挖入链上，但尚未建立最终性阈值     |
| `CONFIRMED` | 是    | 交易已达到强概率最终性并且成功             |
| `RETRYING`  | 否    | 交易事务失败(回滚或重组)，正在由运营商重试/重新提交 |
| `FAILED`    | 是    | 交易已失败且不再重试                  |

### order

在以下情况下触发:

* 订单被下单 (`PLACEMENT`)
* 订单被更新 — 部分被匹配 (`UPDATE`)
* 订单被取消 (`CANCELLATION`)

```json  theme={null}
{
  "asset_id": "52114319501245915516055106046884209969926127482827954674443846427813813222426",
  "associate_trades": null,
  "event_type": "order",
  "id": "0xff354cd7ca7539dfa9c28d90943ab5779a4eac34b9b37a757d7b32bdfb11790b",
  "market": "0xbd31dc8a20211944f6b70f31557f1001557b59905b7738480ca09bd4532f84af",
  "order_owner": "9180014b-33c8-9240-a14b-bdca11c0a465",
  "original_size": "10",
  "outcome": "YES",
  "owner": "9180014b-33c8-9240-a14b-bdca11c0a465",
  "price": "0.57",
  "side": "SELL",
  "size_matched": "0",
  "timestamp": "1672290687",
  "type": "PLACEMENT"
}
```


Built with [Mintlify](https://mintlify.com).