> ## Documentation Index
> Fetch the complete documentation index at: https://docs.polymarket.com/llms.txt
> Use this file to discover all available pages before exploring further.

# 地区限制

> 在 Polymarket API 下单前检查地区限制

由于监管要求和国际制裁合规，Polymarket 限制某些地区的下单操作。在下单前，Builder 应验证用户的地理位置。

<Warning>
  来自受限地区的订单将被拒绝。请在你的应用中实现地区限制检查，以便在用户尝试交易前提供适当的提示。
</Warning>

***

## 地区限制端点

检查请求 IP 地址的地理合规性：

```bash  theme={null}
GET https://polymarket.com/api/geoblock
```

<Note>此端点在 `polymarket.com` 上，不在 API 服务器上。</Note>

### 响应

```json  theme={null}
{
  "blocked": true,
  "ip": "203.0.113.42",
  "country": "US",
  "region": "NY"
}
```

| 字段        | 类型      | 说明                      |
| --------- | ------- | ----------------------- |
| `blocked` | boolean | 用户是否被限制下单               |
| `ip`      | string  | 检测到的 IP 地址              |
| `country` | string  | ISO 3166-1 alpha-2 国家代码 |
| `region`  | string  | 地区/州代码                  |

***

## 受限国家

以下国家被限制在 Polymarket 上下单。标记为 **close-only** 的国家可以平仓现有持仓，但不能开新仓：

| 国家代码 | 国家名称                                 | 状态         |
| ---- | ------------------------------------ | ---------- |
| AU   | Australia                            | Blocked    |
| BE   | Belgium                              | Blocked    |
| BY   | Belarus                              | Blocked    |
| BI   | Burundi                              | Blocked    |
| CF   | Central African Republic             | Blocked    |
| CD   | Congo (Kinshasa)                     | Blocked    |
| CU   | Cuba                                 | Blocked    |
| DE   | Germany                              | Blocked    |
| ET   | Ethiopia                             | Blocked    |
| FR   | France                               | Blocked    |
| GB   | United Kingdom                       | Blocked    |
| IR   | Iran                                 | Blocked    |
| IQ   | Iraq                                 | Blocked    |
| IT   | Italy                                | Blocked    |
| KP   | North Korea                          | Blocked    |
| LB   | Lebanon                              | Blocked    |
| LY   | Libya                                | Blocked    |
| MM   | Myanmar                              | Blocked    |
| NI   | Nicaragua                            | Blocked    |
| NL   | Netherlands                          | Blocked    |
| PL   | Poland                               | Close-only |
| RU   | Russia                               | Blocked    |
| SG   | Singapore                            | Close-only |
| SO   | Somalia                              | Blocked    |
| SS   | South Sudan                          | Blocked    |
| SD   | Sudan                                | Blocked    |
| SY   | Syria                                | Blocked    |
| TH   | Thailand                             | Close-only |
| TW   | Taiwan                               | Close-only |
| UM   | United States Minor Outlying Islands | Blocked    |
| US   | United States                        | Blocked    |
| VE   | Venezuela                            | Blocked    |
| YE   | Yemen                                | Blocked    |
| ZW   | Zimbabwe                             | Blocked    |

***

## 受限地区

除了完全受限的国家外，以下国家内的特定地区也受到限制：

| 国家           | 地区      | 地区代码 |
| ------------ | ------- | ---- |
| Canada (CA)  | Ontario | ON   |
| Ukraine (UA) | Crimea  | 43   |
| Ukraine (UA) | Donetsk | 14   |
| Ukraine (UA) | Luhansk | 09   |

***

## 限制逻辑

地区限制系统包括：

1. **OFAC 制裁国家**：受美国外国资产控制办公室（OFAC）制裁的国家
2. **其他监管限制**：因特定监管合规原因而添加的国家

***

## 服务器基础设施

* **主服务器**：eu-west-2
* **最近的非地区限制区域**：eu-west-1

***

## 使用示例

<Tabs>
  <Tab title="TypeScript">
    ```typescript  theme={null}
    interface GeoblockResponse {
      blocked: boolean;
      ip: string;
      country: string;
      region: string;
    }

    async function checkGeoblock(): Promise<GeoblockResponse> {
      const response = await fetch("https://polymarket.com/api/geoblock");
      return response.json();
    }

    // Usage
    const geo = await checkGeoblock();

    if (geo.blocked) {
      console.log(`Trading not available in ${geo.country}`);
    } else {
      console.log("Trading available");
    }
    ```
  </Tab>

  <Tab title="Python">
    ```python  theme={null}
    import requests

    def check_geoblock() -> dict:
        response = requests.get("https://polymarket.com/api/geoblock")
        return response.json()

    # Usage
    geo = check_geoblock()

    if geo["blocked"]:
        print(f"Trading not available in {geo['country']}")
    else:
        print("Trading available")
    ```
  </Tab>
</Tabs>

***

## 为什么有这些限制

地区限制的实施是为了确保合规：

* 国际制裁和禁运
* 当地金融法规
* 博彩和预测市场法律
* 反洗钱（AML）要求
* 了解你的客户（KYC）法规

如果你认为自己被错误限制或有关于地区可用性的问题，请联系 [Polymarket Support](https://polymarket.com/support)。

***

## 下一步

<CardGroup cols={2}>
  <Card title="身份验证" icon="key" href="/api-reference/authentication">
    了解如何对交易请求进行身份验证。
  </Card>

  <Card title="下单" icon="plus" href="/trading/quickstart">
    开始下单（从合规地区）。
  </Card>
</CardGroup>


Built with [Mintlify](https://mintlify.com).