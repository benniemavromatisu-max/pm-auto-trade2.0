> ## Documentation Index
> Fetch the complete documentation index at: https://docs.polymarket.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Sports WebSocket

> 实时体育比分和比赛状态

Sports WebSocket 提供实时体育赛果更新，包括比分、时段和比赛状态。无需身份验证。

## 端点

```
wss://sports-api.polymarket.com/ws
```

无需发送订阅消息 — 连接后即可开始接收所有活跃体育赛事的数据。

## 心跳

服务器每 5 秒发送一次 `ping`。你需要在 10 秒内回复 `pong`，否则连接将被关闭。

```javascript  theme={null}
ws.onmessage = (event) => {
  if (event.data === "ping") {
    ws.send("pong");
    return;
  }

  // Handle JSON messages...
};
```

## 消息类型

每条消息都是一个包含比赛状态字段的 JSON 对象。

### sport\_result

在以下情况下触发:

* 比赛开始直播
* 比分变化
* 时段变化(例如中场休息、加时赛)
* 比赛结束
* 控球权变化(仅限 NFL 和 CFB)

**NFL (进行中):**

```json  theme={null}
{
  "gameId": 19439,
  "leagueAbbreviation": "nfl",
  "slug": "nfl-lac-buf-2025-01-26",
  "homeTeam": "LAC",
  "awayTeam": "BUF",
  "status": "InProgress",
  "score": "3-16",
  "period": "Q4",
  "elapsed": "5:18",
  "live": true,
  "ended": false,
  "turn": "lac"
}
```

**电子竞技 — CS2 (已结束):**

```json  theme={null}
{
  "gameId": 1317359,
  "leagueAbbreviation": "cs2",
  "slug": "cs2-arcred-the-glecs-2025-07-20",
  "homeTeam": "ARCRED",
  "awayTeam": "The glecs",
  "status": "finished",
  "score": "000-000|2-0|Bo3",
  "period": "2/3",
  "live": false,
  "ended": true,
  "finished_timestamp": "2025-07-20T18:30:00.000Z"
}
```

`finished_timestamp` 字段是一个 ISO 8601 时间戳，仅在 `ended: true` 时出现。

`slug` 字段遵循 `{league}-{team1}-{team2}-{date}` 格式(例如 `nfl-buf-kc-2025-01-26`)。

## 时段值

| 时段                     | 描述                  |
| ---------------------- | ------------------- |
| `1H`                   | 上半场                 |
| `2H`                   | 下半场                 |
| `1Q`, `2Q`, `3Q`, `4Q` | 节(NFL、NBA)          |
| `HT`                   | 中场休息                |
| `FT`                   | 全场结束(常规时间结束)        |
| `FT OT`                | 全场结束(含加时赛)          |
| `FT NR`                | 全场结束，无结果(平局或取消)     |
| `End 1`, `End 2`, ...  | 局结束(MLB)            |
| `1/3`, `2/3`, `3/3`    | Bo3 系列赛中的地图编号(电子竞技) |
| `1/5`, `2/5`, ...      | Bo5 系列赛中的地图编号(电子竞技) |

## 比赛状态值

比赛状态值因运动项目而异:

### NFL

| 状态             | 描述         |
| -------------- | ---------- |
| `Scheduled`    | 比赛尚未开始     |
| `InProgress`   | 比赛正在进行     |
| `Final`        | 比赛在常规时间内结束 |
| `F/OT`         | 加时赛后结束     |
| `Suspended`    | 比赛暂停       |
| `Postponed`    | 比赛延期       |
| `Delayed`      | 比赛延迟       |
| `Canceled`     | 比赛取消       |
| `Forfeit`      | 比赛弃权       |
| `NotNecessary` | 已排期，但不需要   |

### NHL

| 状态             | 描述         |
| -------------- | ---------- |
| `Scheduled`    | 比赛尚未开始     |
| `InProgress`   | 比赛正在进行     |
| `Final`        | 比赛在常规时间内结束 |
| `F/OT`         | 加时赛后结束     |
| `F/SO`         | 点球大战后结束    |
| `Suspended`    | 比赛暂停       |
| `Postponed`    | 比赛延期       |
| `Delayed`      | 比赛延迟       |
| `Canceled`     | 比赛取消       |
| `Forfeit`      | 比赛弃权       |
| `NotNecessary` | 已排期，但不需要   |

### MLB

| 状态             | 描述       |
| -------------- | -------- |
| `Scheduled`    | 比赛尚未开始   |
| `InProgress`   | 比赛正在进行   |
| `Final`        | 比赛结束     |
| `Suspended`    | 比赛暂停     |
| `Delayed`      | 比赛延迟     |
| `Postponed`    | 比赛延期     |
| `Canceled`     | 比赛取消     |
| `Forfeit`      | 比赛弃权     |
| `NotNecessary` | 已排期，但不需要 |

### NBA and CBB

| 状态             | 描述       |
| -------------- | -------- |
| `Scheduled`    | 比赛尚未开始   |
| `InProgress`   | 比赛正在进行   |
| `Final`        | 比赛结束     |
| `F/OT`         | 加时赛后结束   |
| `Suspended`    | 比赛暂停     |
| `Postponed`    | 比赛延期     |
| `Delayed`      | 比赛延迟     |
| `Canceled`     | 比赛取消     |
| `Forfeit`      | 比赛弃权     |
| `NotNecessary` | 已排期，但不需要 |

### CFB

| 状态           | 描述     |
| ------------ | ------ |
| `Scheduled`  | 比赛尚未开始 |
| `InProgress` | 比赛正在进行 |
| `Final`      | 比赛结束   |
| `F/OT`       | 加时赛后结束 |
| `Suspended`  | 比赛暂停   |
| `Postponed`  | 比赛延期   |
| `Delayed`    | 比赛延迟   |
| `Canceled`   | 比赛取消   |
| `Forfeit`    | 比赛弃权   |

### Soccer

| 状态                | 描述          |
| ----------------- | ----------- |
| `Scheduled`       | 比赛尚未开始      |
| `InProgress`      | 比赛正在进行      |
| `Break`           | 中场休息或其他休息时间 |
| `Suspended`       | 比赛暂停        |
| `PenaltyShootout` | 点球大战进行中     |
| `Final`           | 比赛结束        |
| `Awarded`         | 因判决/弃权而授予结果 |
| `Postponed`       | 比赛延期        |
| `Canceled`        | 比赛取消        |

### 电子竞技

| 状态            | 描述     |
| ------------- | ------ |
| `not_started` | 比赛尚未开始 |
| `running`     | 比赛正在进行 |
| `finished`    | 比赛结束   |
| `postponed`   | 比赛延期   |
| `canceled`    | 比赛取消   |

### 网球

| 状态           | 描述     |
| ------------ | ------ |
| `scheduled`  | 比赛尚未开始 |
| `inprogress` | 比赛正在进行 |
| `suspended`  | 比赛暂停   |
| `finished`   | 比赛结束   |
| `postponed`  | 比赛延期   |
| `cancelled`  | 比赛取消   |


Built with [Mintlify](https://mintlify.com).