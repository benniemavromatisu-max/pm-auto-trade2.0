import pytest
from unittest.mock import patch, AsyncMock
from server.credentials import CredentialsManager


def test_credentials_from_env(monkeypatch):
    monkeypatch.setenv("POLY_PRIVATE_KEY", "0x123")
    monkeypatch.setenv("POLY_FUNDER_ADDRESS", "0xabc")
    monkeypatch.setenv("POLY_API_KEY", "key123")
    cm = CredentialsManager()
    assert cm.private_key == "0x123"
    assert cm.funder_address == "0xabc"
    assert cm.api_key == "key123"


def test_credentials_fallback_to_config(monkeypatch):
    monkeypatch.delenv("POLY_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("POLY_API_KEY", raising=False)
    monkeypatch.delenv("POLY_FUNDER_ADDRESS", raising=False)
    cm = CredentialsManager()
    cm._config.credentials.private_key = "0xabc"
    cm._config.credentials.api_key = "abc_key"
    assert cm.private_key == "0xabc"
    assert cm.api_key == "abc_key"


def test_l2_creds_already_in_config(monkeypatch):
    """When api_key already in config, should return it without fetching."""
    monkeypatch.delenv("POLY_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("POLY_FUNDER_ADDRESS", raising=False)
    monkeypatch.delenv("POLY_API_KEY", raising=False)
    cm = CredentialsManager()
    cm._config.credentials.api_key = "saved_key"
    cm._config.credentials.api_secret = "saved_secret"
    cm._config.credentials.api_passphrase = "saved_passphrase"
    # Should NOT try to fetch, just return from config
    assert cm.api_key == "saved_key"
    assert cm.api_secret == "saved_secret"
    assert cm.api_passphrase == "saved_passphrase"
