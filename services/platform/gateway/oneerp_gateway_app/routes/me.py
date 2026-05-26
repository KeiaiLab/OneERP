"""내 정보(Me) 라우트 — 현재 인증된 사용자 정보."""

from __future__ import annotations

from fastapi import APIRouter
from oneerp_core.deps import CurrentUserDep

from ..services.me_service import get_me_payload, update_me_payload

router = APIRouter(prefix="/api/v1/me", tags=["내 정보"])


@router.get("")
def get_me(user: CurrentUserDep) -> dict[str, object]:
    """현재 사용자 + 테넌트 + 권한 + 허용 모듈을 반환한다."""
    return get_me_payload(user)


@router.put("")
def update_me(user: CurrentUserDep, body: dict[str, object]) -> dict[str, str]:
    """본인 정보를 수정한다 (이메일, 성명만)."""
    return update_me_payload(user=user, body=body)
