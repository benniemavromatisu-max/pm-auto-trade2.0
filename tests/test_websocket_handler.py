import pytest
from server.websocket_handler import WSHandler

def test_ws_handler_init():
    handler = WSHandler(host="localhost", port=8766)
    assert handler.host == "localhost"
    assert handler.port == 8766
    assert not handler._running