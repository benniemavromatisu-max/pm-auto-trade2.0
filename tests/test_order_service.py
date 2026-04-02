import pytest
from server.order_service import OrderService, OrderType, Position

def test_position_creation():
    pos = Position(
        direction="YES",
        buy_price=20.0,
        buy_order_id="0x123",
        amount=1.0
    )
    assert pos.direction == "YES"
    assert pos.buy_price == 20.0
    assert pos.status == "open"
    assert pos.sell_order_id is None

def test_calculate_buy_price_with_slippage():
    price = OrderService.calculate_buy_price(20.0, 0.10)
    assert price == 22.0  # 20 * (1 + 0.10)

def test_calculate_sell_price_with_slippage():
    price = OrderService.calculate_sell_price(20.0, 0.10)
    assert price == 18.0  # 20 * (1 - 0.10)