from __future__ import annotations

import os
from dataclasses import dataclass

from server.client212 import Client212


@dataclass(frozen=True, slots=True)
class AccountConfig:
    name: str
    key_id: str
    key_secret: str
    base_url: str


SUPPORTED_ACCOUNTS: frozenset[str] = frozenset({"isa", "invest"})


def _required(value: str, key: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"Missing required environment variable: {key}")
    return cleaned


def _suffix(account: str) -> str:
    return account.strip().upper().replace("-", "_")


def _load_multi_account_configs(accounts_raw: str) -> tuple[dict[str, AccountConfig], str]:
    account_names = [name.strip() for name in accounts_raw.split(",") if name.strip()]
    if not account_names:
        raise ValueError("212_ACCOUNTS is set but does not contain any account names")
    if len(set(account_names)) != len(account_names):
        raise ValueError("212_ACCOUNTS must not contain duplicate account names")

    invalid_accounts = [name for name in account_names if name not in SUPPORTED_ACCOUNTS]
    if invalid_accounts:
        supported = ", ".join(sorted(SUPPORTED_ACCOUNTS))
        invalid = ", ".join(invalid_accounts)
        raise ValueError(f"Unsupported account aliases in 212_ACCOUNTS: {invalid}. Supported values: {supported}")

    default_account = os.getenv("212_DEFAULT_ACCOUNT", account_names[0]).strip()
    if default_account not in account_names:
        raise ValueError("212_DEFAULT_ACCOUNT must be one of 212_ACCOUNTS")

    configs: dict[str, AccountConfig] = {}
    for account in account_names:
        suffix = _suffix(account)
        key_id = _required(os.getenv(f"212_{suffix}_API_KEY_ID", ""), f"212_{suffix}_API_KEY_ID")
        key_secret = _required(os.getenv(f"212_{suffix}_API_KEY_SECRET", ""), f"212_{suffix}_API_KEY_SECRET")
        base_url = _required(os.getenv(f"212_{suffix}_API_BASE_LIVE_URL", ""), f"212_{suffix}_API_BASE_LIVE_URL")
        configs[account] = AccountConfig(name=account, key_id=key_id, key_secret=key_secret, base_url=base_url)

    return configs, default_account


def load_account_configs_from_env() -> tuple[dict[str, AccountConfig], str]:
    accounts_raw = os.getenv("212_ACCOUNTS", "").strip()
    if not accounts_raw:
        raise ValueError("Missing required environment variable: 212_ACCOUNTS")
    return _load_multi_account_configs(accounts_raw)


def build_clients_from_env() -> tuple[dict[str, Client212], str]:
    configs, default_account = load_account_configs_from_env()
    clients = {
        name: Client212(config.key_id, config.key_secret, config.base_url)
        for name, config in configs.items()
    }
    return clients, default_account
