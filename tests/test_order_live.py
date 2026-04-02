"""Test real buy/sell orders with $1 using py-clob-client."""
import asyncio
import os
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import MarketOrderArgs, OrderType, ApiCreds
from server.market_info import MarketInfoManager, get_current_slug


async def test_order():
    private_key = os.getenv("POLY_PRIVATE_KEY")
    funder_address = os.getenv("POLY_FUNDER_ADDRESS")
    signature_type = 1  # POLY_PROXY

    if not private_key or not funder_address:
        print("Missing POLY_PRIVATE_KEY or POLY_FUNDER_ADDRESS")
        return

    print(f"Funder: {funder_address}")
    print(f"Signature type: {signature_type}")

    # Step 1: Create temp client WITHOUT creds to derive L2 credentials
    temp_client = ClobClient(
        host="https://clob.polymarket.com",
        chain_id=137,
        key=private_key,
        signature_type=signature_type,
        funder=funder_address,
    )

    # Derive L2 credentials via L1 auth
    print("\nFetching L2 credentials via L1 auth...")
    api_creds = temp_client.create_or_derive_api_creds()
    print(f"API Key: {api_creds.api_key[:8]}...")
    print(f"API Secret: {api_creds.api_secret[:8]}...")
    print(f"API Passphrase: {api_creds.api_passphrase[:8]}...")

    # Step 2: Create client WITH L2 credentials
    client = ClobClient(
        host="https://clob.polymarket.com",
        chain_id=137,
        key=private_key,
        creds=api_creds,
        signature_type=signature_type,
        funder=funder_address,
    )

    # Get current market
    slug = get_current_slug()
    print(f"\nMarket slug: {slug}")

    manager = MarketInfoManager()
    tokens = await manager.get_token_ids(slug)
    if not tokens:
        print("No tokens found for current market")
        return

    yes_token, no_token = tokens
    print(f"YES token: {yes_token}")
    print(f"NO token: {no_token}")

    # Test BUY YES with $1
    print("\n--- Testing BUY YES ($1) ---")
    try:
        order_args = MarketOrderArgs(
            token_id=yes_token,
            amount=1.0,
            side="BUY",
            price=0.50,
            fee_rate_bps=1000,  # 10% taker fee
        )
        signed_order = client.create_market_order(order_args)
        print(f"Signed order created, signature: {signed_order.signature[:20]}...")

        # Post the order
        result = client.post_order(signed_order, OrderType.FOK)
        print(f"Post result: {result}")
    except Exception as e:
        print(f"Buy error: {type(e).__name__}: {e}")

    # Test SELL YES with 2 shares (what we bought for $1 at price 0.50)
    print("\n--- Testing SELL YES (2 shares @ $0.50) ---")
    try:
        order_args = MarketOrderArgs(
            token_id=yes_token,
            amount=2.0,  # 2 shares bought with $1 at 0.50 price
            side="SELL",
            price=0.50,
            fee_rate_bps=1000,
        )
        signed_order = client.create_market_order(order_args)
        result = client.post_order(signed_order, OrderType.FOK)
        print(f"Post result: {result}")
    except Exception as e:
        print(f"Sell error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(test_order())
