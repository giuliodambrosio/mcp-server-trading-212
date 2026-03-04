from __future__ import annotations

import pytest

from server.account_config import build_clients_from_env, load_account_configs_from_env


def _set_env(monkeypatch: pytest.MonkeyPatch, key: str, value: str) -> None:
    monkeypatch.setenv(key, value)


def test_load_account_configs_supports_isa_and_invest(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch, "212_ACCOUNTS", "isa,invest")
    _set_env(monkeypatch, "212_DEFAULT_ACCOUNT", "isa")
    _set_env(monkeypatch, "212_ISA_API_KEY_ID", "isa-id")
    _set_env(monkeypatch, "212_ISA_API_KEY_SECRET", "isa-secret")
    _set_env(monkeypatch, "212_ISA_API_BASE_LIVE_URL", "https://live.trading212.com/api/v0/")
    _set_env(monkeypatch, "212_INVEST_API_KEY_ID", "invest-id")
    _set_env(monkeypatch, "212_INVEST_API_KEY_SECRET", "invest-secret")
    _set_env(monkeypatch, "212_INVEST_API_BASE_LIVE_URL", "https://live.trading212.com/api/v0/")

    configs, default_account = load_account_configs_from_env()

    assert list(configs.keys()) == ["isa", "invest"]
    assert default_account == "isa"


def test_load_account_configs_allows_single_supported_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch, "212_ACCOUNTS", "invest")
    _set_env(monkeypatch, "212_DEFAULT_ACCOUNT", "invest")
    _set_env(monkeypatch, "212_INVEST_API_KEY_ID", "invest-id")
    _set_env(monkeypatch, "212_INVEST_API_KEY_SECRET", "invest-secret")
    _set_env(monkeypatch, "212_INVEST_API_BASE_LIVE_URL", "https://live.trading212.com/api/v0/")

    configs, default_account = load_account_configs_from_env()

    assert list(configs.keys()) == ["invest"]
    assert default_account == "invest"


def test_load_account_configs_rejects_unsupported_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch, "212_ACCOUNTS", "cash")
    with pytest.raises(ValueError, match="Unsupported account aliases"):
        load_account_configs_from_env()


def test_load_account_configs_rejects_empty_alias_set(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch, "212_ACCOUNTS", ",,,")
    with pytest.raises(ValueError, match="does not contain any account names"):
        load_account_configs_from_env()


def test_load_account_configs_rejects_duplicate_aliases(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch, "212_ACCOUNTS", "isa,isa")
    with pytest.raises(ValueError, match="must not contain duplicate"):
        load_account_configs_from_env()


def test_load_account_configs_rejects_default_outside_declared_set(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch, "212_ACCOUNTS", "isa")
    _set_env(monkeypatch, "212_DEFAULT_ACCOUNT", "invest")
    _set_env(monkeypatch, "212_ISA_API_KEY_ID", "isa-id")
    _set_env(monkeypatch, "212_ISA_API_KEY_SECRET", "isa-secret")
    _set_env(monkeypatch, "212_ISA_API_BASE_LIVE_URL", "https://live.trading212.com/api/v0/")

    with pytest.raises(ValueError, match="212_DEFAULT_ACCOUNT must be one of 212_ACCOUNTS"):
        load_account_configs_from_env()


def test_load_account_configs_requires_account_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch, "212_ACCOUNTS", "isa")
    _set_env(monkeypatch, "212_DEFAULT_ACCOUNT", "isa")
    monkeypatch.delenv("212_ISA_API_KEY_ID", raising=False)
    _set_env(monkeypatch, "212_ISA_API_KEY_SECRET", "isa-secret")
    _set_env(monkeypatch, "212_ISA_API_BASE_LIVE_URL", "https://live.trading212.com/api/v0/")

    with pytest.raises(ValueError, match="212_ISA_API_KEY_ID"):
        load_account_configs_from_env()


def test_load_account_configs_requires_accounts_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("212_ACCOUNTS", raising=False)
    with pytest.raises(ValueError, match="212_ACCOUNTS"):
        load_account_configs_from_env()


def test_build_clients_from_env_returns_clients(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch, "212_ACCOUNTS", "isa")
    _set_env(monkeypatch, "212_DEFAULT_ACCOUNT", "isa")
    _set_env(monkeypatch, "212_ISA_API_KEY_ID", "isa-id")
    _set_env(monkeypatch, "212_ISA_API_KEY_SECRET", "isa-secret")
    _set_env(monkeypatch, "212_ISA_API_BASE_LIVE_URL", "https://live.trading212.com/api/v0/")

    clients, default_account = build_clients_from_env()

    assert default_account == "isa"
    assert list(clients.keys()) == ["isa"]
