> ## Documentation Index
> Fetch the complete documentation index at: https://docs.polymarket.com/llms.txt
> Use this file to discover all available pages before exploring further.

# 客户端与 SDK

> 与 Polymarket 交互的官方开源库

Polymarket 提供 TypeScript、Python 和 Rust 的官方开源客户端。三者都支持完整的 CLOB API，包括市场数据、订单管理和身份验证。

## 安装

<CodeGroup>
  ```bash TypeScript theme={null}
  npm install @polymarket/clob-client ethers@5
  ```

  ```bash Python theme={null}
  pip install py-clob-client
  ```

  ```bash Rust theme={null}
  cargo add polymarket-client-sdk
  ```
</CodeGroup>

## 快速示例

<CodeGroup>
  ```typescript TypeScript theme={null}
  import { ClobClient } from "@polymarket/clob-client";

  const client = new ClobClient(
    "https://clob.polymarket.com",
    137,
    signer,
    apiCreds,
  );

  const markets = await client.getMarkets();
  ```

  ```python Python theme={null}
  from py_clob_client.client import ClobClient

  client = ClobClient(
      "https://clob.polymarket.com",
      key=private_key,
      chain_id=137,
      creds=api_creds,
  )

  markets = client.get_markets()
  ```
</CodeGroup>

## 源代码

| 语言         | 包                         | 仓库                                                                                   |
| ---------- | ------------------------- | ------------------------------------------------------------------------------------ |
| TypeScript | `@polymarket/clob-client` | [github.com/Polymarket/clob-client](https://github.com/Polymarket/clob-client)       |
| Python     | `py-clob-client`          | [github.com/Polymarket/py-clob-client](https://github.com/Polymarket/py-clob-client) |
| Rust       | `polymarket-client-sdk`   | [github.com/Polymarket/rs-clob-client](https://github.com/Polymarket/rs-clob-client) |

每个仓库的 `/examples` 目录中包含可运行的示例。

## Builder SDK

如果你通过 [Builder Program](/builders/overview) 构建应用，还可以使用额外的签名 SDK：

| 语言         | 包                                 | 仓库                                                                                                   |
| ---------- | --------------------------------- | ---------------------------------------------------------------------------------------------------- |
| TypeScript | `@polymarket/builder-signing-sdk` | [github.com/Polymarket/builder-signing-sdk](https://github.com/Polymarket/builder-signing-sdk)       |
| Python     | `py_builder_signing_sdk`          | [github.com/Polymarket/py-builder-signing-sdk](https://github.com/Polymarket/py-builder-signing-sdk) |

使用详情请参阅[订单归因](/trading/orders/attribution)。

## Relayer SDK

对于使用代理钱包的[免 Gas 交易](/trading/gasless)，Relayer 客户端负责通过 Polymarket 的 relayer 提交交易：

| 语言         | 包                                    | 仓库                                                                                                         |
| ---------- | ------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| TypeScript | `@polymarket/builder-relayer-client` | [github.com/Polymarket/builder-relayer-client](https://github.com/Polymarket/builder-relayer-client)       |
| Python     | `py-builder-relayer-client`          | [github.com/Polymarket/py-builder-relayer-client](https://github.com/Polymarket/py-builder-relayer-client) |

## 下一步

<CardGroup cols={2}>
  <Card title="快速开始" icon="rocket" href="/quickstart">
    设置客户端并下你的第一笔订单。
  </Card>

  <Card title="身份验证" icon="lock" href="/api-reference/authentication">
    了解 L1/L2 身份验证和 API 凭证。
  </Card>
</CardGroup>


Built with [Mintlify](https://mintlify.com).