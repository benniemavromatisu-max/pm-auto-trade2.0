> ## Documentation Index
> Fetch the complete documentation index at: https://docs.polymarket.com/llms.txt
> Use this file to discover all available pages before exploring further.

# 简介

> Polymarket API 概览

Polymarket API 提供对全球最大预测市场的编程访问。平台由三个独立的 API 组成，各自处理不同的领域。

***

## API

<CardGroup cols={1}>
  <Card title="Gamma API" icon="database">
    **`https://gamma-api.polymarket.com`**

    市场、事件、标签、系列、评论、体育、搜索和公开个人资料。这是发现和浏览市场数据的主要 API。
  </Card>

  <Card title="Data API" icon="chart-line">
    **`https://data-api.polymarket.com`**

    用户持仓、交易、活动、持有者数据、未平仓合约、排行榜和 Builder 分析。
  </Card>

  <Card title="CLOB API" icon="arrows-rotate">
    **`https://clob.polymarket.com`**

    订单簿数据、价格、中间价、价差和价格历史。同时处理下单、撤单和其他交易操作。交易端点需要[身份验证](/api-reference/authentication)。
  </Card>
</CardGroup>

<Info>
  另有一个独立的 **Bridge API**（`https://bridge.polymarket.com`）处理充值和提现。Bridge 不由 Polymarket 直接运营，而是 fun.xyz 服务的代理。
</Info>

***

## 身份验证

Gamma API 和 Data API 完全公开——不需要身份验证。

CLOB API 同时包含公开端点（订单簿、价格）和需要验证的端点（订单管理）。详情请参阅[身份验证](/api-reference/authentication)。

***

## 下一步

<CardGroup cols={2}>
  <Card title="身份验证" icon="key" href="/api-reference/authentication">
    了解如何为交易端点验证请求。
  </Card>

  <Card title="客户端与 SDK" icon="cube" href="/api-reference/clients-sdks">
    官方 TypeScript、Python 和 Rust 库。
  </Card>
</CardGroup>


Built with [Mintlify](https://mintlify.com).