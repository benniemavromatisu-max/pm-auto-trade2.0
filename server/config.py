"""Configuration management for the trading bot."""
import json
import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class StrategyConfig:
    buy_price_min: float = 18
    buy_price_max: float = 22
    stop_loss: float = 13
    take_profit: float = 35
    slippage: float = 0.10
    buy_window_minutes: int = 2
    force_close_minutes: int = 1
    rounds_per_market: int = 3
    buy_amount: float = 1.0


@dataclass
class Credentials:
    private_key: str = ""
    api_key: str = ""
    api_secret: str = ""
    api_passphrase: str = ""
    funder_address: str = ""


@dataclass
class Config:
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    credentials: Credentials = field(default_factory=Credentials)


def validate_config(config: dict) -> List[str]:
    """Validate configuration and return list of errors."""
    errors = []
    if "strategy" not in config:
        errors.append("Missing 'strategy' section")
        return errors

    s = config["strategy"]
    if s.get("buy_price_min", 0) >= s.get("buy_price_max", 100):
        errors.append("buy_price_min must be < buy_price_max")
    if s.get("stop_loss", 0) >= s.get("take_profit", 100):
        errors.append("stop_loss must be < take_profit")
    if not 0 <= s.get("slippage", 0) <= 1:
        errors.append("slippage must be between 0 and 1")

    return errors


class ConfigManager:
    DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "config.json")

    def __init__(self, config_path: str = None):
        self.config_path = config_path or self.DEFAULT_PATH
        self.config = Config()
        self.load()

    @property
    def strategy(self):
        return self.config.strategy

    @property
    def credentials(self):
        return self.config.credentials

    def load(self):
        """Load configuration from JSON file."""
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                data = json.load(f)
                if "strategy" in data:
                    for key, value in data["strategy"].items():
                        if hasattr(self.config.strategy, key):
                            setattr(self.config.strategy, key, value)
                if "credentials" in data:
                    for key, value in data["credentials"].items():
                        if hasattr(self.config.credentials, key):
                            setattr(self.config.credentials, key, value)

    def save(self):
        """Save configuration to JSON file (atomic write)."""
        data = {
            "strategy": {
                "buy_price_min": self.config.strategy.buy_price_min,
                "buy_price_max": self.config.strategy.buy_price_max,
                "stop_loss": self.config.strategy.stop_loss,
                "take_profit": self.config.strategy.take_profit,
                "slippage": self.config.strategy.slippage,
                "buy_window_minutes": self.config.strategy.buy_window_minutes,
                "force_close_minutes": self.config.strategy.force_close_minutes,
                "rounds_per_market": self.config.strategy.rounds_per_market,
                "buy_amount": self.config.strategy.buy_amount,
            },
            "credentials": {
                "private_key": self.config.credentials.private_key,
                "api_key": self.config.credentials.api_key,
                "api_secret": self.config.credentials.api_secret,
                "api_passphrase": self.config.credentials.api_passphrase,
                "funder_address": self.config.credentials.funder_address,
            }
        }
        tmp_path = self.config_path + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, self.config_path)