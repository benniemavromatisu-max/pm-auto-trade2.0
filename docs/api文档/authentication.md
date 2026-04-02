> ## Documentation Index
> Fetch the complete documentation index at: https://docs.polymarket.com/llms.txt
> Use this file to discover all available pages before exploring further.

# 身份验证

> 如何对 CLOB API 请求进行身份验证

CLOB API 使用两级身份验证：\*\*L1（私钥）\*\*和 **L2（API Key）**。两种方式都可以通过 CLOB 客户端或 REST API 完成。

## 公开 vs 需要验证

<CardGroup cols={1}>
  <Card title="公开（无需验证）" icon="unlock">
    **Gamma API**、**Data API** 和 CLOB 读取端点（订单簿、价格、价差）不需要身份验证。
  </Card>

  <Card title="需要验证（CLOB）" icon="lock">
    CLOB 交易端点（下单、撤单、心跳）需要全部 5 个 `POLY_*` L2 HTTP header。
  </Card>
</CardGroup>

***

## 两级身份验证模型

CLOB 使用两级身份验证：L1（私钥）和 L2（API Key）。两种方式都可以通过 CLOB 客户端或 REST API 完成。

### L1 身份验证 - 私钥

L1 身份验证使用钱包的私钥签署一个 EIP-712 消息，用于请求头。它证明了对私钥的所有权和控制权。私钥始终由用户控制，所有交易活动都是非托管的。

**用于：**

* 创建 API 凭证
* 派生现有的 API 凭证
* 本地签署和创建用户订单

### L2 身份验证 - API 凭证

L2 使用从 L1 身份验证生成的 API 凭证（apiKey、secret、passphrase）。这些仅用于验证发送到 CLOB API 的请求。请求使用 HMAC-SHA256 签名。

**用于：**

* 取消或获取用户的活跃订单
* 检查用户的余额和授权
* 提交用户签名的订单

<Info>
  即使使用了 L2 身份验证 header，创建用户订单的方法仍然需要用户签署订单 payload。
</Info>

***

## 获取 API 凭证

在发送需要验证的请求之前，你需要使用 L1 身份验证获取 API 凭证。

### 使用 SDK - 推荐

<Tabs>
  <Tab title="TypeScript">
    ```typescript  theme={null}
    import { ClobClient } from "@polymarket/clob-client";
    import { Wallet } from "ethers"; // v5.8.0

    const client = new ClobClient(
      "https://clob.polymarket.com",
      137, // Polygon mainnet
      new Wallet(process.env.PRIVATE_KEY)
    );

    // Creates new credentials or derives existing ones
    const credentials = await client.createOrDeriveApiKey();

    console.log(credentials);
    // {
    //   apiKey: "550e8400-e29b-41d4-a716-446655440000",
    //   secret: "base64EncodedSecretString",
    //   passphrase: "randomPassphraseString"
    // }
    ```
  </Tab>

  <Tab title="Python">
    ```python  theme={null}
    from py_clob_client.client import ClobClient
    import os

    client = ClobClient(
        host="https://clob.polymarket.com",
        chain_id=137,  # Polygon mainnet
        key=os.getenv("PRIVATE_KEY")
    )

    # Creates new credentials or derives existing ones
    credentials = client.create_or_derive_api_creds()

    print(credentials)
    # {
    #     "apiKey": "550e8400-e29b-41d4-a716-446655440000",
    #     "secret": "base64EncodedSecretString",
    #     "passphrase": "randomPassphraseString"
    # }
    ```
  </Tab>
</Tabs>

<Warning>
  \*\*永远不要将私钥提交到版本控制系统。\*\*请始终使用环境变量或安全的密钥管理系统。
</Warning>

### 使用 REST API

虽然我们强烈建议使用提供的客户端来处理签名和身份验证，但以下内容适用于选择不使用 [Python](https://github.com/Polymarket/py-clob-client) 或 [TypeScript](https://github.com/Polymarket/clob-client) 客户端的开发者。

**创建 API 凭证**

```bash  theme={null}
POST https://clob.polymarket.com/auth/api-key
```

**派生 API 凭证**

```bash  theme={null}
GET https://clob.polymarket.com/auth/derive-api-key
```

所需的 L1 header：

| Header           | 说明              |
| ---------------- | --------------- |
| `POLY_ADDRESS`   | Polygon 签名者地址   |
| `POLY_SIGNATURE` | CLOB EIP-712 签名 |
| `POLY_TIMESTAMP` | 当前 UNIX 时间戳     |
| `POLY_NONCE`     | Nonce（默认值: 0）   |

`POLY_SIGNATURE` 通过签署以下 EIP-712 结构生成：

<Accordion title="EIP-712 签名示例">
  <CodeGroup>
    ```typescript TypeScript theme={null}
    const domain = {
      name: "ClobAuthDomain",
      version: "1",
      chainId: chainId, // Polygon Chain ID 137
    };

    const types = {
      ClobAuth: [
        { name: "address", type: "address" },
        { name: "timestamp", type: "string" },
        { name: "nonce", type: "uint256" },
        { name: "message", type: "string" },
      ],
    };

    const value = {
      address: signingAddress, // The Signing address
      timestamp: ts,            // The CLOB API server timestamp
      nonce: nonce,             // The nonce used
      message: "This message attests that I control the given wallet",
    };

    const sig = await signer._signTypedData(domain, types, value);
    ```

    ```python Python theme={null}
    domain = {
        "name": "ClobAuthDomain",
        "version": "1",
        "chainId": chainId,  # Polygon Chain ID 137
    }

    types = {
        "ClobAuth": [
            {"name": "address", "type": "address"},
            {"name": "timestamp", "type": "string"},
            {"name": "nonce", "type": "uint256"},
            {"name": "message", "type": "string"},
        ]
    }

    value = {
        "address": signingAddress,  # The signing address
        "timestamp": ts,            # The CLOB API server timestamp
        "nonce": nonce,             # The nonce used
        "message": "This message attests that I control the given wallet",
    }

    sig = signer.sign_typed_data(domain, types, value)
    ```
  </CodeGroup>
</Accordion>

参考实现：

* [TypeScript](https://github.com/Polymarket/clob-client/blob/main/src/signing/eip712.ts)
* [Python](https://github.com/Polymarket/py-clob-client/blob/main/py_clob_client/signing/eip712.py)

响应：

```json  theme={null}
{
  "apiKey": "550e8400-e29b-41d4-a716-446655440000",
  "secret": "base64EncodedSecretString",
  "passphrase": "randomPassphraseString"
}
```

**L2 身份验证需要这三个值。**

***

## L2 身份验证 Header

所有交易端点需要以下 5 个 header：

| Header            | 说明                     |
| ----------------- | ---------------------- |
| `POLY_ADDRESS`    | Polygon 签名者地址          |
| `POLY_SIGNATURE`  | 请求的 HMAC 签名            |
| `POLY_TIMESTAMP`  | 当前 UNIX 时间戳            |
| `POLY_API_KEY`    | 用户的 API `apiKey` 值     |
| `POLY_PASSPHRASE` | 用户的 API `passphrase` 值 |

L2 的 `POLY_SIGNATURE` 是使用用户 API 凭证的 `secret` 值创建的 HMAC-SHA256 签名。参考实现可在 [TypeScript](https://github.com/Polymarket/clob-client/blob/main/src/signing/hmac.ts) 和 [Python](https://github.com/Polymarket/py-clob-client/blob/main/py_clob_client/signing/hmac.py) 客户端中找到。

### CLOB 客户端 - L2

<Tabs>
  <Tab title="TypeScript">
    ```typescript  theme={null}
    import { ClobClient } from "@polymarket/clob-client";
    import { Wallet } from "ethers"; // v5.8.0

    const client = new ClobClient(
      "https://clob.polymarket.com",
      137,
      new Wallet(process.env.PRIVATE_KEY),
      apiCreds, // Generated from L1 auth, API credentials enable L2 methods
      1, // signatureType explained below
      funderAddress // funder explained below
    );

    // Now you can trade!
    const order = await client.createAndPostOrder(
      { tokenID: "123456", price: 0.65, size: 100, side: "BUY" },
      { tickSize: "0.01", negRisk: false }
    );
    ```
  </Tab>

  <Tab title="Python">
    ```python  theme={null}
    from py_clob_client.client import ClobClient
    import os

    client = ClobClient(
        host="https://clob.polymarket.com",
        chain_id=137,
        key=os.getenv("PRIVATE_KEY"),
        creds=api_creds,  # Generated from L1 auth, API credentials enable L2 methods
        signature_type=1,  # signatureType explained below
        funder=os.getenv("FUNDER_ADDRESS") # funder explained below
    )

    # Now you can trade!
    order = client.create_and_post_order(
        {"token_id": "123456", "price": 0.65, "size": 100, "side": "BUY"},
        {"tick_size": "0.01", "neg_risk": False}
    )
    ```
  </Tab>
</Tabs>

<Info>
  即使使用了 L2 身份验证 header，创建用户订单的方法仍然需要用户签署订单 payload。
</Info>

***

## 签名类型和 Funder

初始化 L2 客户端时，你必须指定钱包的 **signatureType** 和持有资金的 **funder** 地址：

| 签名类型         | 值   | 说明                                                                                |
| ------------ | --- | --------------------------------------------------------------------------------- |
| EOA          | `0` | 标准 Ethereum 钱包（MetaMask）。Funder 即 EOA 地址，需要 POL 来支付链上交易的 gas 费。                   |
| POLY\_PROXY  | `1` | 仅用于通过 Magic Link 邮箱/Google 登录的用户的自定义代理钱包。使用此类型需要用户从 Polymarket.com 导出私钥并导入到你的应用中。 |
| GNOSIS\_SAFE | `2` | Gnosis Safe 多签代理钱包（最常见）。对于不属于其他两种类型的新用户或回归用户，请使用此类型。                              |

<Tip>
  Polymarket.com 上显示给用户的钱包地址是代理钱包地址，应作为 funder 使用。这些地址可以确定性地派生，或者你可以代表用户部署它们。这些代理钱包会在用户首次登录 Polymarket.com 时自动部署。
</Tip>

***

## 安全最佳实践

<AccordionGroup>
  <Accordion title="永远不要暴露私钥">
    将私钥存储在环境变量或安全的密钥管理系统中。永远不要将它们提交到版本控制系统。

    ```bash  theme={null}
    # .env (never commit this file)
    PRIVATE_KEY=0x...
    ```
  </Accordion>

  <Accordion title="在服务器端实现请求签名">
    永远不要在客户端代码中暴露你的 API secret。所有需要身份验证的请求都应从你的后端发起。
  </Accordion>
</AccordionGroup>

***

## 故障排除

<AccordionGroup>
  <Accordion title="错误 - INVALID_SIGNATURE">
    你的钱包私钥不正确或格式不对。

    **解决方案：**

    * 验证你的私钥是有效的十六进制字符串（以 "0x" 开头）
    * 确保你使用的是目标地址对应的正确密钥
    * 检查密钥是否具有正确的权限
  </Accordion>

  <Accordion title="错误 - NONCE_ALREADY_USED">
    你提供的 nonce 已被用于创建 API key。

    **解决方案：**

    * 使用相同的 nonce 调用 `deriveApiKey()` 来获取现有凭证
    * 或使用不同的 nonce 调用 `createApiKey()`
  </Accordion>

  <Accordion title="错误 - Invalid Funder Address">
    你的 funder 地址不正确或与你的钱包不匹配。

    \*\*解决方案：\*\*在 [polymarket.com/settings](https://polymarket.com/settings) 查看你的 Polymarket 个人资料地址。

    如果地址不存在或用户从未登录过 Polymarket.com，请先部署地址，然后再创建 L2 身份验证。
  </Accordion>

  <Accordion title="凭证和 nonce 都丢失了">
    很遗憾，没有 nonce 就无法恢复丢失的 API 凭证。你需要创建新的凭证：

    ```typescript  theme={null}
    // Create fresh credentials with a new nonce
    const newCreds = await client.createApiKey();
    // Save the nonce this time!
    ```
  </Accordion>
</AccordionGroup>

***

## 下一步

<CardGroup cols={2}>
  <Card title="下你的第一笔订单" icon="plus" href="/trading/quickstart">
    了解如何创建和提交订单。
  </Card>

  <Card title="地区限制" icon="globe" href="/api-reference/geoblock">
    按地区检查交易可用性。
  </Card>
</CardGroup>


Built with [Mintlify](https://mintlify.com).