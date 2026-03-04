from __future__ import annotations

from server.errors import ResourceNotFoundError, Trading212APIError


def test_trading212_api_error_string_with_json_payload():
    err = Trading212APIError(status_code=400, method="GET", url="https://example.com/x", payload={"error": "bad"})
    text = str(err)
    assert "Trading212 API error 400 on GET https://example.com/x." in text
    assert 'payload={"error": "bad"}' in text


def test_trading212_api_error_string_with_unserializable_payload():
    err = Trading212APIError(status_code=500, method="POST", url="https://example.com/y", payload={1, 2, 3})
    text = str(err)
    assert "Trading212 API error 500 on POST https://example.com/y." in text
    assert "payload={" in text


def test_resource_not_found_error_string():
    err = ResourceNotFoundError("instrument", "AAPL_US_EQ")
    assert str(err) == "instrument 'AAPL_US_EQ' was not found."
