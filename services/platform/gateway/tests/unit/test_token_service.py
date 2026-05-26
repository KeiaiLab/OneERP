from __future__ import annotations

from oneerp_gateway_app.services.token_service import create_refresh_token_payload


def test_refresh_payload은_refresh_type을_가진다() -> None:
    payload = create_refresh_token_payload(username="demo", tenant_id="t1")
    assert payload["type"] == "refresh"
    assert payload["sub"] == "demo"
    assert payload["tenant_id"] == "t1"
