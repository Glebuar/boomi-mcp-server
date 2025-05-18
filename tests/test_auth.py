import os
from boomi_mcp import auth

class DummyBoomi:
    def __init__(self, account, user, secret):
        self.args = (account, user, secret)

def test_get_client_uses_env(monkeypatch):
    monkeypatch.setenv("BOOMI_ACCOUNT", "acct")
    monkeypatch.setenv("BOOMI_USER", "user")
    monkeypatch.setenv("BOOMI_SECRET", "secret")
    monkeypatch.setattr(auth, "Boomi", DummyBoomi)

    client = auth.get_client()
    assert isinstance(client, DummyBoomi)
    assert client.args == ("acct", "user", "secret")
