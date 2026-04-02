"""Credentials management - loads from env vars, auto-fetches L2 creds via L1 auth."""
import os
import asyncio
from dataclasses import dataclass
from typing import Optional

from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds

from server.config import ConfigManager, Config


@dataclass
class L2Credentials:
    api_key: str
    secret: str
    passphrase: str


class CredentialsManager:
    """Manages API credentials from environment or config, auto-fetches L2 via L1."""

    AUTH_LOCK = asyncio.Lock()

    def __init__(self, config: Optional[Config] = None):
        self.config_manager = ConfigManager() if config is None else None
        self._l2_creds: Optional[L2Credentials] = None

    @property
    def _config(self) -> Config:
        if self.config_manager is None:
            raise RuntimeError("No config provided")
        return self.config_manager.config

    @property
    def private_key(self) -> str:
        return os.getenv("POLY_PRIVATE_KEY") or self._config.credentials.private_key

    @property
    def funder_address(self) -> str:
        return os.getenv("POLY_FUNDER_ADDRESS") or self._config.credentials.funder_address

    @property
    def api_key(self) -> str:
        # Priority: env var > L2 cache > config
        env_key = os.getenv("POLY_API_KEY")
        if env_key:
            return env_key
        if self._l2_creds:
            return self._l2_creds.api_key
        return self._config.credentials.api_key

    @property
    def api_secret(self) -> str:
        env_secret = os.getenv("POLY_API_SECRET")
        if env_secret:
            return env_secret
        if self._l2_creds:
            return self._l2_creds.secret
        return self._config.credentials.api_secret

    @property
    def api_passphrase(self) -> str:
        env_pass = os.getenv("POLY_API_PASSPHRASE")
        if env_pass:
            return env_pass
        if self._l2_creds:
            return self._l2_creds.passphrase
        return self._config.credentials.api_passphrase

    def _get_or_fetch_creds(self) -> Optional[L2Credentials]:
        if self._l2_creds is not None:
            return self._l2_creds
        if self._config.credentials.api_key:
            return L2Credentials(
                api_key=self._config.credentials.api_key,
                secret=self._config.credentials.api_secret,
                passphrase=self._config.credentials.api_passphrase,
            )
        return None

    async def fetch_and_save_l2_credentials(self) -> Optional[L2Credentials]:
        """L1 auth: use private key to derive L2 credentials, save to config."""
        private_key = self.private_key
        if not private_key:
            print("CredentialsManager: POLY_PRIVATE_KEY not set, skipping L2 credential fetch")
            return None

        if not self.funder_address:
            print("CredentialsManager: POLY_FUNDER_ADDRESS not set, skipping L2 credential fetch")
            return None

        async with self.AUTH_LOCK:
            # Double-check after acquiring lock
            if self._l2_creds is not None:
                return self._l2_creds

            print("CredentialsManager: Fetching L2 credentials via L1 auth...")
            try:
                client = ClobClient(
                    host="https://clob.polymarket.com",
                    chain_id=137,
                    key=private_key,
                )
                creds: ApiCreds = client.create_or_derive_api_creds()

                self._l2_creds = L2Credentials(
                    api_key=creds.api_key,
                    secret=creds.api_secret,
                    passphrase=creds.api_passphrase,
                )

                # Save to config for persistence
                self._config.credentials.api_key = creds.api_key
                self._config.credentials.api_secret = creds.api_secret
                self._config.credentials.api_passphrase = creds.api_passphrase
                if self.config_manager:
                    self.config_manager.save()

                print(f"CredentialsManager: L2 credentials fetched and saved (api_key={creds.api_key[:8]}...)")
                return self._l2_creds

            except Exception as e:
                print(f"CredentialsManager: Failed to fetch L2 credentials: {e}")
                return None

    def clear_l2_creds(self):
        """Clear cached L2 credentials (useful for testing or re-auth)."""
        self._l2_creds = None
