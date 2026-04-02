import pytest
import os
import tempfile
import json
from server.config import ConfigManager, StrategyConfig, validate_config

def test_strategy_config_defaults():
    cfg = StrategyConfig()
    assert cfg.buy_price_min == 18
    assert cfg.buy_price_max == 22
    assert cfg.stop_loss == 13
    assert cfg.take_profit == 35
    assert cfg.slippage == 0.10

def test_validate_config_valid():
    cfg = {
        "strategy": {
            "buy_price_min": 18,
            "buy_price_max": 22,
            "stop_loss": 13,
            "take_profit": 35,
            "slippage": 0.10,
            "buy_window_minutes": 2,
            "force_close_minutes": 1,
            "rounds_per_market": 3,
            "buy_amount": 1.0
        }
    }
    errors = validate_config(cfg)
    assert len(errors) == 0

def test_validate_config_invalid_range():
    cfg = {
        "strategy": {
            "buy_price_min": 25,
            "buy_price_max": 22,
            "stop_loss": 13,
            "take_profit": 35,
            "slippage": 0.10,
            "buy_window_minutes": 2,
            "force_close_minutes": 1,
            "rounds_per_market": 3,
            "buy_amount": 1.0
        }
    }
    errors = validate_config(cfg)
    assert len(errors) > 0

def test_config_manager_save_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, "config.json")
        cfg = ConfigManager(config_file)
        cfg.strategy.buy_price_min = 20
        cfg.save()
        cfg2 = ConfigManager(config_file)
        cfg2.load()
        assert cfg2.strategy.buy_price_min == 20