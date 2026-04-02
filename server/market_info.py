"""Market information and slug management."""
import json
import time
import httpx
from typing import Optional, Dict, Any

GAMMA_API = "https://gamma-api.polymarket.com"


def get_current_slug() -> str:
    """Get the current market slug based on current time."""
    now = time.time()
    period = 300  # 5 minutes
    end_timestamp = int(now // period) * period + period
    return f"btc-updown-5m-{end_timestamp}"


def get_next_slug() -> str:
    """Get the next market slug."""
    now = time.time()
    period = 300
    next_end = int(now // period) * period + 600
    return f"btc-updown-5m-{next_end}"


def get_slug_end_timestamp(slug: str) -> int:
    """Extract end timestamp from slug."""
    return int(slug.split("-")[-1])


def get_slug_start_timestamp(slug: str) -> int:
    """Get market start timestamp (5 minutes before end)."""
    return get_slug_end_timestamp(slug) - 300


class MarketInfoManager:
    """Fetches and caches market information from Gamma API."""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_time: Dict[str, float] = {}
        self._cache_ttl = 60  # Cache for 60 seconds

    async def get_market_info(self, slug: str) -> Optional[Dict[str, Any]]:
        """Fetch market info from Gamma API."""
        if slug in self._cache:
            if time.time() - self._cache_time[slug] < self._cache_ttl:
                return self._cache[slug]

        url = f"{GAMMA_API}/markets/slug/{slug}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    self._cache[slug] = data
                    self._cache_time[slug] = time.time()
                    return data
            except Exception as e:
                print(f"Error fetching market info: {e}")
                return None

        return None

    async def get_token_ids(self, slug: str) -> Optional[tuple]:
        """Get YES and NO token IDs for a market."""
        info = await self.get_market_info(slug)
        if not info:
            return None

        clob_token_ids = info.get("clobTokenIds", "")
        if not clob_token_ids:
            return None

        # Parse JSON array string like '["token1", "token2"]'
        try:
            tokens = json.loads(clob_token_ids)
            if isinstance(tokens, list) and len(tokens) >= 2:
                return tokens[0], tokens[1]  # (yes_token, no_token)
        except json.JSONDecodeError:
            # Fallback to comma-separated
            tokens = clob_token_ids.split(",")
            if len(tokens) >= 2:
                return tokens[0], tokens[1]

        return None