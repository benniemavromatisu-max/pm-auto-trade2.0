> ## Documentation Index
> Fetch the complete documentation index at: https://docs.polymarket.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Real-Time Data Socket

> 通过 WebSocket 流式传输评论和加密货币价格

Polymarket Real-Time Data Socket (RTDS) 是一个基于 WebSocket 的流式服务，提供**评论**和**加密货币价格**的实时更新。

<Card title="TypeScript client" icon="github" href="https://github.com/Polymarket/real-time-data-client">
  官方 RTDS TypeScript 客户端 (`real-time-data-client`)。
</Card>

## 端点

```
wss://ws-live-data.polymarket.com
```

某些用户特定的流可能需要使用你的钱包地址进行 `gamma_auth` 身份验证。

## 订阅

发送 JSON 消息来订阅数据流:

```json  theme={null}
{
  "action": "subscribe",
  "subscriptions": [
    {
      "topic": "topic_name",
      "type": "message_type",
      "filters": "optional_filter_string",
      "gamma_auth": {
        "address": "wallet_address"
      }
    }
  ]
}
```

要取消订阅，发送相同结构的消息，将 `"action"` 改为 `"unsubscribe"`。

你可以在不断开连接的情况下添加、删除和修改订阅。每 5 秒发送一次 `PING` 消息以维持连接。

<Note>仅支持下文记录的订阅类型。</Note>

## 消息结构

所有消息都遵循以下结构:

```json  theme={null}
{
  "topic": "string",
  "type": "string",
  "timestamp": "number",
  "payload": "object"
}
```

| 字段          | 类型     | 描述                                      |
| ----------- | ------ | --------------------------------------- |
| `topic`     | string | 订阅主题(例如 `crypto_prices`、`comments`)     |
| `type`      | string | 消息类型/事件(例如 `update`、`reaction_created`) |
| `timestamp` | number | 消息发送时的 Unix 时间戳(毫秒)                     |
| `payload`   | object | 特定于事件的数据对象                              |

## 加密货币价格

来自两个来源的实时加密货币价格数据:**Binance** 和 **Chainlink**。无需身份验证。

### Binance 来源

订阅所有交易对:

```json  theme={null}
{
  "action": "subscribe",
  "subscriptions": [
    {
      "topic": "crypto_prices",
      "type": "update"
    }
  ]
}
```

使用逗号分隔的过滤器订阅特定交易对:

```json  theme={null}
{
  "action": "subscribe",
  "subscriptions": [
    {
      "topic": "crypto_prices",
      "type": "update",
      "filters": "solusdt,btcusdt,ethusdt"
    }
  ]
}
```

交易对使用小写连接格式(例如 `solusdt`、`btcusdt`)。

**Solana 价格更新:**

```json  theme={null}
{
  "topic": "crypto_prices",
  "type": "update",
  "timestamp": 1753314064237,
  "payload": {
    "symbol": "solusdt",
    "timestamp": 1753314064213,
    "value": 189.55
  }
}
```

**Bitcoin 价格更新:**

```json  theme={null}
{
  "topic": "crypto_prices",
  "type": "update",
  "timestamp": 1753314088421,
  "payload": {
    "symbol": "btcusdt",
    "timestamp": 1753314088395,
    "value": 67234.50
  }
}
```

### Chainlink 来源

<Tip>
  **正在交易 15 分钟加密货币市场？** 获取由 Chainlink 赞助的 Chainlink API 密钥，并获得入门支持。填写[此表单](https://pm-ds-request.streams.chain.link/)。
</Tip>

订阅所有交易对:

```json  theme={null}
{
  "action": "subscribe",
  "subscriptions": [
    {
      "topic": "crypto_prices_chainlink",
      "type": "*",
      "filters": ""
    }
  ]
}
```

使用 JSON 过滤器订阅特定交易对:

```json  theme={null}
{
  "action": "subscribe",
  "subscriptions": [
    {
      "topic": "crypto_prices_chainlink",
      "type": "*",
      "filters": "{\"symbol\":\"eth/usd\"}"
    }
  ]
}
```

交易对使用斜杠分隔格式(例如 `eth/usd`、`btc/usd`)。

**Ethereum 价格更新:**

```json  theme={null}
{
  "topic": "crypto_prices_chainlink",
  "type": "update",
  "timestamp": 1753314064237,
  "payload": {
    "symbol": "eth/usd",
    "timestamp": 1753314064213,
    "value": 3456.78
  }
}
```

**Bitcoin 价格更新:**

```json  theme={null}
{
  "topic": "crypto_prices_chainlink",
  "type": "update",
  "timestamp": 1753314088421,
  "payload": {
    "symbol": "btc/usd",
    "timestamp": 1753314088395,
    "value": 67234.50
  }
}
```

### 价格 Payload 字段

| 字段          | 类型     | 描述                                                                                          |
| ----------- | ------ | ------------------------------------------------------------------------------------------- |
| `symbol`    | string | 交易对符号。**Binance**: 小写连接(例如 `solusdt`、`btcusdt`)。**Chainlink**: 斜杠分隔(例如 `eth/usd`、`btc/usd`) |
| `timestamp` | number | 价格记录时间，Unix 毫秒时间戳                                                                           |
| `value`     | number | 计价货币中的当前价格值                                                                                 |

### 支持的交易对

**Binance 来源** — 小写连接格式:

* `btcusdt` — Bitcoin 对 USDT
* `ethusdt` — Ethereum 对 USDT
* `solusdt` — Solana 对 USDT
* `xrpusdt` — XRP 对 USDT

**Chainlink 来源** — 斜杠分隔格式:

* `btc/usd` — Bitcoin 对 USD
* `eth/usd` — Ethereum 对 USD
* `sol/usd` — Solana 对 USD
* `xrp/usd` — XRP 对 USD

## 评论

Polymarket 平台上的实时评论事件，包括新评论、回复、反应和删除。某些用户特定数据可能需要 Gamma 身份验证。

### 订阅

```json  theme={null}
{
  "action": "subscribe",
  "subscriptions": [
    {
      "topic": "comments",
      "type": "comment_created"
    }
  ]
}
```

### 消息类型

| 类型                 | 描述         |
| ------------------ | ---------- |
| `comment_created`  | 用户创建新评论或回复 |
| `comment_removed`  | 评论被移除或删除   |
| `reaction_created` | 用户对评论添加反应  |
| `reaction_removed` | 反应从评论中移除   |

### comment\_created

当用户发布新评论或回复现有评论时触发。

```json  theme={null}
{
  "topic": "comments",
  "type": "comment_created",
  "timestamp": 1753454975808,
  "payload": {
    "body": "That's a good point about the definition.",
    "createdAt": "2025-07-25T14:49:35.801298Z",
    "id": "1763355",
    "parentCommentID": "1763325",
    "parentEntityID": 18396,
    "parentEntityType": "Event",
    "profile": {
      "baseAddress": "0xce533188d53a16ed580fd5121dedf166d3482677",
      "displayUsernamePublic": true,
      "name": "salted.caramel",
      "proxyWallet": "0x4ca749dcfa93c87e5ee23e2d21ff4422c7a4c1ee",
      "pseudonym": "Adored-Disparity"
    },
    "reactionCount": 0,
    "replyAddress": "0x0bda5d16f76cd1d3485bcc7a44bc6fa7db004cdd",
    "reportCount": 0,
    "userAddress": "0xce533188d53a16ed580fd5121dedf166d3482677"
  }
}
```

对上述评论的回复 — 注意 `parentCommentID` 引用了父评论:

```json  theme={null}
{
  "topic": "comments",
  "type": "comment_created",
  "timestamp": 1753454985123,
  "payload": {
    "body": "I agree, the resolution criteria should be clearer.",
    "createdAt": "2025-07-25T14:49:45.120000Z",
    "id": "1763356",
    "parentCommentID": "1763355",
    "parentEntityID": 18396,
    "parentEntityType": "Event",
    "profile": {
      "baseAddress": "0x1234567890abcdef1234567890abcdef12345678",
      "displayUsernamePublic": true,
      "name": "trader",
      "proxyWallet": "0x9876543210fedcba9876543210fedcba98765432",
      "pseudonym": "Bright-Analysis"
    },
    "reactionCount": 0,
    "replyAddress": "0x0bda5d16f76cd1d3485bcc7a44bc6fa7db004cdd",
    "reportCount": 0,
    "userAddress": "0x1234567890abcdef1234567890abcdef12345678"
  }
}
```

### 评论 Payload 字段

| 字段                 | 类型     | 描述                                   |
| ------------------ | ------ | ------------------------------------ |
| `body`             | string | 评论的文本内容                              |
| `createdAt`        | string | 评论创建时的 ISO 8601 时间戳                  |
| `id`               | string | 此评论的唯一标识符                            |
| `parentCommentID`  | string | 如果这是回复，则为父评论的 ID(顶级评论为 null)         |
| `parentEntityID`   | number | 父实体(事件、市场等)的 ID                      |
| `parentEntityType` | string | 父实体的类型(`Event`、`Market`)             |
| `profile`          | object | 评论作者的个人资料信息                          |
| `reactionCount`    | number | 此评论当前的反应数量                           |
| `replyAddress`     | string | 用于回复的 Polygon 地址(可能与 userAddress 不同) |
| `reportCount`      | number | 此评论当前的举报数量                           |
| `userAddress`      | string | 评论作者的 Polygon 地址                     |

### Profile 对象字段

| 字段                      | 类型      | 描述          |
| ----------------------- | ------- | ----------- |
| `baseAddress`           | string  | 用户资料地址      |
| `displayUsernamePublic` | boolean | 用户名是否公开显示   |
| `name`                  | string  | 用户的显示名称     |
| `proxyWallet`           | string  | 用于交易的代理钱包地址 |
| `pseudonym`             | string  | 为用户生成的假名    |

### 评论层级结构

评论支持嵌套分层:

* **顶级评论**: `parentCommentID` 为 null 或为空
* **回复评论**: `parentCommentID` 包含父评论的 ID
* 所有评论都与 `parentEntityID` 和 `parentEntityType`(`Event` 或 `Market`)关联

## 故障排除

<Accordion title="连接意外断开">
  每 5 秒发送一次 `PING` 消息以保持连接活跃。连接错误将触发自动重连尝试。
</Accordion>

<Accordion title="订阅后未收到消息">
  验证你的订阅消息是否为有效的 JSON，并包含正确的 `action`、`topic` 和 `type` 字段。无效的订阅消息可能导致连接关闭。
</Accordion>

<Accordion title="身份验证失败">
  如果订阅用户特定的流，请确保你的 `gamma_auth` 对象包含有效的钱包 `address`。身份验证失败将阻止订阅受保护的主题。
</Accordion>


Built with [Mintlify](https://mintlify.com).