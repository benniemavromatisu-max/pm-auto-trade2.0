> ## Documentation Index
> Fetch the complete documentation index at: https://docs.polymarket.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Market 频道

> 实时订单簿、价格和交易数据

用于市场数据更新的公共频道（Level 2 价格数据）。使用 asset ID 订阅以接收订单簿快照、价格变化、交易执行和市场事件。

## 端点

```
wss://ws-subscriptions-clob.polymarket.com/ws/market
```

## 订阅

```json  theme={null}
{
  "assets_ids": ["<token_id_1>", "<token_id_2>"],
  "type": "market",
  "custom_feature_enabled": true
}
```

设置 `custom_feature_enabled: true` 以接收 `best_bid_ask`、`new_market` 和 `market_resolved` 事件。

## 消息类型

每条消息都包含一个 `event_type` 字段来标识类型。

### book

首次订阅市场时以及发生影响订单簿的交易时触发。

```json  theme={null}
{
  "event_type": "book",
  "asset_id": "65818619657568813474341868652308942079804919287380422192892211131408793125422",
  "market": "0xbd31dc8a20211944f6b70f31557f1001557b59905b7738480ca09bd4532f84af",
  "bids": [
    { "price": ".48", "size": "30" },
    { "price": ".49", "size": "20" },
    { "price": ".50", "size": "15" }
  ],
  "asks": [
    { "price": ".52", "size": "25" },
    { "price": ".53", "size": "60" },
    { "price": ".54", "size": "10" }
  ],
  "timestamp": "123456789000",
  "hash": "0x0...."
}
```

### price\_change

下新订单或取消订单时触发。

```json  theme={null}
{
  "market": "0x5f65177b394277fd294cd75650044e32ba009a95022d88a0c1d565897d72f8f1",
  "price_changes": [
    {
      "asset_id": "71321045679252212594626385532706912750332728571942532289631379312455583992563",
      "price": "0.5",
      "size": "200",
      "side": "BUY",
      "hash": "56621a121a47ed9333273e21c83b660cff37ae50",
      "best_bid": "0.5",
      "best_ask": "1"
    },
    {
      "asset_id": "52114319501245915516055106046884209969926127482827954674443846427813813222426",
      "price": "0.5",
      "size": "200",
      "side": "SELL",
      "hash": "1895759e4df7a796bf4f1c5a5950b748306923e2",
      "best_bid": "0",
      "best_ask": "0.5"
    }
  ],
  "timestamp": "1757908892351",
  "event_type": "price_change"
}
```

`size` 为 `"0"` 表示该价格级别已从订单簿中移除。

### tick\_size\_change

市场的最小价格变动单位发生变化时触发。当订单簿价格达到极限值时会发生这种情况：price > 0.96 或 price \< 0.04。

```json  theme={null}
{
  "event_type": "tick_size_change",
  "asset_id": "65818619657568813474341868652308942079804919287380422192892211131408793125422",
  "market": "0xbd31dc8a20211944f6b70f31557f1001557b59905b7738480ca09bd4532f84af",
  "old_tick_size": "0.01",
  "new_tick_size": "0.001",
  "timestamp": "100000000"
}
```

### last\_trade\_price

Maker 和 Taker 订单匹配，产生交易事件时触发。

```json  theme={null}
{
  "asset_id": "114122071509644379678018727908709560226618148003371446110114509806601493071694",
  "event_type": "last_trade_price",
  "fee_rate_bps": "0",
  "market": "0x6a67b9d828d53862160e470329ffea5246f338ecfffdf2cab45211ec578b0347",
  "price": "0.456",
  "side": "BUY",
  "size": "219.217767",
  "timestamp": "1750428146322"
}
```

### best\_bid\_ask

<Note>需要 `custom_feature_enabled: true`。</Note>

市场的最优买价或卖价发生变化时触发。

```json  theme={null}
{
  "event_type": "best_bid_ask",
  "market": "0x0005c0d312de0be897668695bae9f32b624b4a1ae8b140c49f08447fcc74f442",
  "asset_id": "85354956062430465315924116860125388538595433819574542752031640332592237464430",
  "best_bid": "0.73",
  "best_ask": "0.77",
  "spread": "0.04",
  "timestamp": "1766789469958"
}
```

### new\_market

<Note>需要 `custom_feature_enabled: true`。</Note>

创建新市场时触发。

```json  theme={null}
{
  "id": "1031769",
  "question": "Will NVIDIA (NVDA) close above $240 end of January?",
  "market": "0x311d0c4b6671ab54af4970c06fcf58662516f5168997bdda209ec3db5aa6b0c1",
  "slug": "nvda-above-240-on-january-30-2026",
  "description": "This market will resolve to \"Yes\" if the official closing price...",
  "assets_ids": [
    "76043073756653678226373981964075571318267289248134717369284518995922789326425",
    "31690934263385727664202099278545688007799199447969475608906331829650099442770"
  ],
  "outcomes": ["Yes", "No"],
  "event_message": {
    "id": "125819",
    "ticker": "nvda-above-in-january-2026",
    "slug": "nvda-above-in-january-2026",
    "title": "Will NVIDIA (NVDA) close above ___ end of January?",
    "description": "This market will resolve to \"Yes\" if the official closing price..."
  },
  "timestamp": "1766790415550",
  "event_type": "new_market"
}
```

### market\_resolved

<Note>需要 `custom_feature_enabled: true`。</Note>

市场判定时触发。

```json  theme={null}
{
  "id": "1031769",
  "question": "Will NVIDIA (NVDA) close above $240 end of January?",
  "market": "0x311d0c4b6671ab54af4970c06fcf58662516f5168997bdda209ec3db5aa6b0c1",
  "slug": "nvda-above-240-on-january-30-2026",
  "description": "This market will resolve to \"Yes\" if the official closing price...",
  "assets_ids": [
    "76043073756653678226373981964075571318267289248134717369284518995922789326425",
    "31690934263385727664202099278545688007799199447969475608906331829650099442770"
  ],
  "outcomes": ["Yes", "No"],
  "winning_asset_id": "76043073756653678226373981964075571318267289248134717369284518995922789326425",
  "winning_outcome": "Yes",
  "event_message": {
    "id": "125819",
    "ticker": "nvda-above-in-january-2026",
    "slug": "nvda-above-in-january-2026",
    "title": "Will NVIDIA (NVDA) close above ___ end of January?",
    "description": "This market will resolve to \"Yes\" if the official closing price..."
  },
  "timestamp": "1766790415550",
  "event_type": "market_resolved"
}
```


Built with [Mintlify](https://mintlify.com).