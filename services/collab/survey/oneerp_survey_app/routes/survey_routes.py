"""설문/투표 커스텀 라우터 — 배포, 마감, 응답 제출, 결과 조회 API.

CRUD는 EntityMeta 자동 생성, 이 라우터는 비즈니스 로직 전용.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from oneerp_core.deps import CurrentUserDep
from oneerp_core.permissions import require_permission

from ..services.poll_service import PollService
from ..services.survey_service import SurveyService

router = APIRouter(prefix="/api/v1", tags=["설문/투표"])


# ── 설문 배포/마감 ──


@router.post(
    "/surveys/{survey_id}/publish",
    dependencies=[Depends(require_permission("survey:write"))],
)
def publish_survey(survey_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """설문을 배포한다 (draft → active)."""
    svc = SurveyService(user.tenant_id)
    return svc.publish_survey(survey_id)


@router.post(
    "/surveys/{survey_id}/close",
    dependencies=[Depends(require_permission("survey:write"))],
)
def close_survey(survey_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """설문을 마감한다 (active → closed)."""
    svc = SurveyService(user.tenant_id)
    return svc.close_survey(survey_id)


# ── 설문 응답 ──


@router.post("/surveys/{survey_id}/responses", status_code=201)
def submit_response(
    survey_id: str,
    body: dict[str, Any],
    user: CurrentUserDep,
) -> dict[str, Any]:
    """설문 응답을 제출한다."""
    svc = SurveyService(user.tenant_id)
    return svc.submit_response(survey_id, body)


# ── 설문 결과 ──


@router.get(
    "/surveys/{survey_id}/results",
    dependencies=[Depends(require_permission("survey:read"))],
)
def get_survey_results(
    survey_id: str,
    user: CurrentUserDep,
    group_by: str = Query(default="", description="교차 분석 기준"),
) -> dict[str, Any]:
    """설문 결과를 조회한다."""
    svc = SurveyService(user.tenant_id)
    if group_by:
        return svc.get_results_grouped(survey_id, group_by=group_by)
    return {"survey_id": survey_id, "message": "결과 조회 성공"}


# ── 템플릿으로 생성 ──


@router.post(
    "/surveys/from-template",
    status_code=201,
    dependencies=[Depends(require_permission("survey:create"))],
)
def create_from_template(
    body: dict[str, Any],
    user: CurrentUserDep,
) -> dict[str, Any]:
    """템플릿으로 설문을 생성한다."""
    template_id = body.pop("template_id", "")
    svc = SurveyService(user.tenant_id)
    return svc.create_from_template(template_id, body)


# ── 투표 ──


@router.post("/polls/{poll_id}/vote", status_code=201)
def cast_vote(
    poll_id: str,
    body: dict[str, Any],
    user: CurrentUserDep,
) -> dict[str, Any]:
    """투표한다."""
    svc = PollService(user.tenant_id)
    return svc.cast_vote(poll_id, body)


@router.get("/polls/{poll_id}/results")
def get_poll_results(
    poll_id: str,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """투표 결과를 조회한다."""
    svc = PollService(user.tenant_id)
    return svc.get_results(poll_id)


@router.post(
    "/polls/{poll_id}/close",
    dependencies=[Depends(require_permission("poll:write"))],
)
def close_poll(poll_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """투표를 마감한다."""
    svc = PollService(user.tenant_id)
    return svc.close_poll(poll_id)
