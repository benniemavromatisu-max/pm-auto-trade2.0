import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from server.price_poller import PricePoller

@pytest.mark.asyncio
async def test_price_poller_init():
    poller = PricePoller("yes_token", "no_token", lambda y, n: None)
    assert poller.yes_token == "yes_token"
    assert poller.no_token == "no_token"
    assert poller.POLL_INTERVAL == 0.5

@pytest.mark.asyncio
async def test_calculate_prices():
    collected = []
    def callback(yes, no):
        collected.append((yes, no))

    poller = PricePoller("yes_token", "no_token", callback)

    mock_response = {
        "yes_token": {"BUY": 0.21},
        "no_token": {"SELL": 0.79}
    }

    with patch('httpx.AsyncClient') as mock_client:
        mock_response_obj = Mock()
        mock_response_obj.status_code = 200
        mock_response_obj.json = Mock(return_value=mock_response)
        mock_instance = AsyncMock()
        mock_instance.post = AsyncMock(return_value=mock_response_obj)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

        await poller._fetch_prices()

    assert len(collected) == 1
    assert collected[0] == (0.21, 0.79)