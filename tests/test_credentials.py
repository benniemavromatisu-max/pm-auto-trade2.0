import pytest
from server.credentials import CredentialsManager

def test_credentials_from_env(monkeypatch):
    monkeypatch.setenv("POLY_PRIVATE_KEY", "0x123")
    monkeypatch.setenv("POLY_API_KEY", "key123")
    cm = CredentialsManager()
    assert cm.private_key == "0x123"
    assert cm.api_key == "key123"

def test_credentials_from_config(monkeypatch):
    monkeypatch.delenv("POLY_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("POLY_API_KEY", raising=False)
    cm = CredentialsManager()
    cm.config.credentials.private_key = "0xabc"
    cm.config.credentials.api_key = "abc_key"
    assert cm.private_key == "0xabc"