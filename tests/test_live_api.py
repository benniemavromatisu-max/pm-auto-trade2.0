"""Live API tests against real Polymarket endpoints (no trading, read-only)."""
import asyncio
import pytest
import time
from server.market_info import get_current_slug, get_slug_end_timestamp
from server.price_poller import PricePoller


@pytest.mark.asyncio
async def test_live_price_fetch_current_market():
    """Fetch real prices from current active BTC 5m market."""
    slug = get_current_slug()
    print(f"\n[Live] Current slug: {slug}")

    # Get token IDs for current market
    from server.market_info import MarketInfoManager
    manager = MarketInfoManager()
    tokens = await manager.get_token_ids(slug)
    assert tokens is not None, f"No tokens found for slug {slug}"
    yes_token, no_token = tokens
    print(f"[Live] YES token: {yes_token}, NO token: {no_token}")

    # Poll prices once
    prices_received = []

    def capture_price(yes_price, no_price):
        prices_received.append((yes_price, no_price))

    poller = PricePoller(yes_token, no_token, capture_price)
    await poller._fetch_prices()

    assert len(prices_received) == 1, "Should receive exactly one price update"
    yes_price, no_price = prices_received[0]
    print(f"[Live] YES price: {yes_price}, NO price: {no_price}")

    # Validate price ranges (should be between 0 and 1)
    assert 0 <= yes_price <= 1, f"YES price {yes_price} out of range"
    assert 0 <= no_price <= 1, f"NO price {no_price} out of range"

    # YES + NO should approximately equal 1 (minus spread)
    total = yes_price + no_price
    print(f"[Live] YES + NO = {total}")
    assert 0.9 <= total <= 1.1, f"Price spread abnormal: {total}"

    print("[Live] Price fetch test PASSED")


@pytest.mark.asyncio
async def test_live_market_info():
    """Fetch real market info from Gamma API."""
    slug = get_current_slug()
    print(f"\n[Live] Testing market info for: {slug}")

    from server.market_info import MarketInfoManager
    manager = MarketInfoManager()
    info = await manager.get_market_info(slug)

    assert info is not None, f"Failed to fetch market info for {slug}"
    print(f"[Live] Market question: {info.get('question', 'N/A')}")
    print(f"[Live] CLOB tokens: {info.get('clobTokenIds', 'N/A')}")
    print(f"[Live] End date: {info.get('endDate', 'N/A')}")

    end_ts = get_slug_end_timestamp(slug)
    print(f"[Live] Slug end timestamp: {end_ts} ({(end_ts - time.time()) / 60:.1f} min from now)")

    print("[Live] Market info test PASSED")


if __name__ == "__main__":
    asyncio.run(test_live_market_info())
    asyncio.run(test_live_price_fetch_current_market())
