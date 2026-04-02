import pytest
import time
from server.market_info import MarketInfoManager, get_current_slug, get_next_slug

def test_get_current_slug_format():
    slug = get_current_slug()
    assert slug.startswith("btc-updown-5m-")
    parts = slug.split("-")
    timestamp = int(parts[-1])
    assert timestamp > time.time()
    assert (timestamp - int(time.time())) % 300 in (0, 300 - (int(time.time()) % 300))

def test_get_next_slug():
    current = get_current_slug()
    next_slug = get_next_slug()
    assert next_slug != current
    current_ts = int(current.split("-")[-1])
    next_ts = int(next_slug.split("-")[-1])
    assert next_ts > current_ts

@pytest.mark.asyncio
async def test_fetch_market_info():
    manager = MarketInfoManager()
    slug = get_current_slug()
    info = await manager.get_market_info(slug)
    assert info is not None