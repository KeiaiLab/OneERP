from __future__ import annotations

from oneerp_gateway_app.services.me_service import filter_me_update_fields


def test_me_update는_허용된_필드만_남긴다() -> None:
    assert filter_me_update_fields({"email": "a@b.c", "roles": ["admin"]}) == {"email": "a@b.c"}
