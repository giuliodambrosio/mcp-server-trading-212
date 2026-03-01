import json

import pytest

from server.resources import resource_account_balance, resource_account_info


class FakeReadService:
    async def get_account_info(self):
        return {"currency": "GBP"}

    async def get_balance(self):
        return {"free": 100.0}


@pytest.mark.asyncio
async def test_account_info_resource_has_envelope_fields():
    payload = json.loads(await resource_account_info(FakeReadService()))

    assert payload["data"] == {"currency": "GBP"}
    assert payload["source_endpoint"] == "equity/account/info"
    assert "generated_at" in payload


@pytest.mark.asyncio
async def test_account_balance_resource_has_envelope_fields():
    payload = json.loads(await resource_account_balance(FakeReadService()))

    assert payload["data"] == {"free": 100.0}
    assert payload["source_endpoint"] == "equity/account/cash"
    assert "generated_at" in payload
