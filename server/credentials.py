"""Credentials management - loads from env vars or config."""
import os
from server.config import ConfigManager


class CredentialsManager:
    """Manages API credentials from environment or config."""

    def __init__(self):
        self.config = ConfigManager()

    @property
    def private_key(self) -> str:
        return os.getenv("POLY_PRIVATE_KEY") or self.config.credentials.private_key

    @property
    def api_key(self) -> str:
        return os.getenv("POLY_API_KEY") or self.config.credentials.api_key

    @property
    def api_secret(self) -> str:
        return os.getenv("POLY_API_SECRET") or self.config.credentials.api_secret

    @property
    def api_passphrase(self) -> str:
        return os.getenv("POLY_API_PASSPHRASE") or self.config.credentials.api_passphrase

    @property
    def funder_address(self) -> str:
        return os.getenv("POLY_FUNDER_ADDRESS") or self.config.credentials.funder_address