"""팝업 공지 커스텀 라우트.

L2-spec 5.6 API 계약에 따른 비즈니스 엔드포인트.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["팝업 공지"])


@router.get("/popup-notices/active")
async def get_active_popups() -> dict[str, list[dict[str, Any]]]:
    """현재 사용자에게 표시할 활성 팝업 조회."""
    from oneerp_board_app.services.popup_service import PopupService

    svc = PopupService("T1")
    popups = svc.get_active_popups(user_id="current_user")
    return {"popups": popups}


@router.post("/popup-notices/{popup_id}/confirm")
async def confirm_popup(popup_id: str) -> dict[str, Any]:
    """팝업 공지 확인 처리."""
    from oneerp_board_app.services.popup_service import PopupService

    svc = PopupService("T1")
    return svc.confirm_popup(popup_id, user_id="current_user")
