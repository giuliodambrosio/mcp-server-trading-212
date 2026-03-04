import json

import pytest

from server.resources import resource_account_balance, resource_account_info


class FakeReadService:
    async def get_account_info(self, account: str):
        assert account == "isa"
        return {"currency": "GBP"}

    async def get_balance(self, account: str):
        assert account == "isa"
        return {"free": 100.0}


@pytest.mark.asyncio
async def test_account_info_resource_has_envelope_fields():
    payload = json.loads(await resource_account_info(FakeReadService(), "isa"))

    assert payload["data"] == {"currency": "GBP"}
    assert payload["source_endpoint"] == "equity/account/info"
    assert "generated_at" in payload


@pytest.mark.asyncio
async def test_account_balance_resource_has_envelope_fields():
    payload = json.loads(await resource_account_balance(FakeReadService(), "isa"))

    assert payload["data"] == {"free": 100.0}
    assert payload["source_endpoint"] == "equity/account/cash"
    assert "generated_at" in payload
