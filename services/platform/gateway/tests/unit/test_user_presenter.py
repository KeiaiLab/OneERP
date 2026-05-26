from __future__ import annotations

from oneerp_gateway_app.services.user_presenter import status_badge_for


def test_inactive_user는_inactive_badge를_가진다() -> None:
    assert status_badge_for({"is_active": False}) == "inactive_user"
