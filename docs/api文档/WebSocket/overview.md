> ## Documentation Index
> Fetch the complete documentation index at: https://docs.polymarket.com/llms.txt
> Use this file to discover all available pages before exploring further.

# 概述

> 通过 WebSocket 获取实时市场数据和交易更新

Polymarket 提供 WebSocket 频道，用于近实时流式传输订单簿数据、交易和个人订单活动。共有四个可用频道：`market`、`user`、`sports` 和 `RTDS`（Real-Time Data Socket）。

## 频道

| 频道                                  | 端点                                                     | 需要认证 |
| ----------------------------------- | ------------------------------------------------------ | ---- |
| Market                              | `wss://ws-subscriptions-clob.polymarket.com/ws/market` | 否    |
| User                                | `wss://ws-subscriptions-clob.polymarket.com/ws/user`   | 是    |
| Sports                              | `wss://sports-api.polymarket.com/ws`                   | 否    |
| [RTDS](/market-data/websocket/rtds) | `wss://ws-live-data.polymarket.com`                    | 可选   |

### Market 频道

| 类型                 | 说明         | 自定义功能 |
| ------------------ | ---------- | ----- |
| `book`             | 完整订单簿快照    | 否     |
| `price_change`     | 价格级别更新     | 否     |
| `tick_size_change` | 最小价格变动单位变化 | 否     |
| `last_trade_price` | 交易执行       | 否     |
| `best_bid_ask`     | 最优价格更新     | 是     |
| `new_market`       | 新市场创建      | 是     |
| `market_resolved`  | 市场判定       | 是     |

标记为"自定义功能"的类型需要在订阅时设置 `custom_feature_enabled: true`。

### User 频道

| 类型      | 说明                            |
| ------- | ----------------------------- |
| `trade` | 交易生命周期更新（MATCHED → CONFIRMED） |
| `order` | 订单下单、更新和取消                    |

### Sports

| 类型             | 说明           |
| -------------- | ------------ |
| `sport_result` | 实时比赛分数、时段和状态 |

## 订阅

连接后发送订阅消息以指定你想接收的数据。

### Market 频道

```json  theme={null}
{
  "assets_ids": [
    "21742633143463906290569050155826241533067272736897614950488156847949938836455",
    "48331043336612883890938759509493159234755048973500640148014422747788308965732"
  ],
  "type": "market",
  "custom_feature_enabled": true
}
```

| 字段                       | 类型        | 说明                                                    |
| ------------------------ | --------- | ----------------------------------------------------- |
| `assets_ids`             | string\[] | 要订阅的代币 ID                                             |
| `type`                   | string    | 频道标识符                                                 |
| `custom_feature_enabled` | boolean   | 启用 `best_bid_ask`、`new_market` 和 `market_resolved` 事件 |

### User 频道

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

<Note>
  `auth` 字段（`apiKey`、`secret`、`passphrase`）**仅在 user 频道中需要**。对于 market 频道，这些字段是可选的，可以省略。
</Note>

| 字段        | 类型        | 说明                                     |
| --------- | --------- | -------------------------------------- |
| `auth`    | object    | API 凭证（`apiKey`、`secret`、`passphrase`） |
| `markets` | string\[] | 要接收事件的 condition ID                    |
| `type`    | string    | 频道标识符                                  |

<Note>
  user 频道通过 **condition ID**（市场标识符）订阅，而不是 asset ID。每个市场有一个 condition ID，但有两个 asset ID（Yes 和 No 代币）。
</Note>

### Sports 频道

无需订阅消息。连接后即可开始接收所有活跃体育赛事的数据。

## 动态订阅

无需重新连接即可修改订阅。

### 订阅更多资产

```json  theme={null}
{
  "assets_ids": ["new_asset_id_1", "new_asset_id_2"],
  "operation": "subscribe",
  "custom_feature_enabled": true
}
```

### 取消订阅资产

```json  theme={null}
{
  "assets_ids": ["asset_id_to_remove"],
  "operation": "unsubscribe"
}
```

对于 user 频道，使用 `markets` 而不是 `assets_ids`：

```json  theme={null}
{
  "markets": ["0x1234...condition_id"],
  "operation": "subscribe"
}
```

## 心跳

### Market 和 User 频道

每 10 秒发送一次 `PING`。服务器会响应 `PONG`。

```
PING
```

### Sports 频道

服务器每 5 秒发送一次 `ping`。你需要在 10 秒内响应 `pong`。

```
pong
```

<Warning>
  如果你在 10 秒内没有响应服务器的 ping，连接将被关闭。
</Warning>

## 故障排除

<Accordion title="连接在打开后立即关闭">
  连接后立即发送有效的订阅消息。服务器可能会关闭在超时时间内未订阅的连接。
</Accordion>

<Accordion title="连接在约 10 秒后断开">
  你没有发送心跳。对于 market/user 频道，每 10 秒发送一次 `PING`；对于 sports 频道，用 `pong` 响应服务器的 `ping`。
</Accordion>

<Accordion title="未收到任何消息">
  1. 验证你的 asset ID 或 condition ID 是否正确 2. 检查市场是否处于活跃状态（未判定） 3. 如果期望接收 `best_bid_ask`、`new_market` 或 `market_resolved` 事件，请设置 `custom_feature_enabled: true`
</Accordion>

<Accordion title="认证失败 - user 频道">
  验证你的 API 凭证是否正确且未过期。
</Accordion>


Built with [Mintlify](https://mintlify.com).