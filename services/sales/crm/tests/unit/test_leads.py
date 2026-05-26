"""리드(Lead) API 엔드포인트 테스트."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

if TYPE_CHECKING:
    from types import ModuleType

    from fastapi.testclient import TestClient


def test_리드_생성(test_client: TestClient, leads_mod: ModuleType) -> None:
    """리드 생성 API가 정상 동작하는지 검증한다."""
    mock_repo = MagicMock()
    mock_repo.insert.return_value = "LEAD-2026-00001"

    with (
        patch.object(leads_mod, "_get_repo", return_value=mock_repo),
        patch("oneerp_crm_app.routes.leads.generate_name", return_value="LEAD-2026-00001"),
    ):
        response = test_client.post(
            "/api/v1/leads",
            json={
                "lead_name": "홍길동",
                "company_name": "테스트 회사",
                "email": "hong@test.com",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "LEAD-2026-00001"


def test_리드_목록_조회(test_client: TestClient, leads_mod: ModuleType) -> None:
    """리드 목록 API가 페이지네이션과 함께 동작하는지 검증한다."""
    mock_repo = MagicMock()
    mock_repo.find_many.return_value = [{"_id": "LEAD-2026-00001", "lead_name": "홍길동"}]
    mock_repo.count.return_value = 1

    with patch.object(leads_mod, "_get_repo", return_value=mock_repo):
        response = test_client.get("/api/v1/leads")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["data"]) == 1


def test_리드_상세_조회(test_client: TestClient, leads_mod: ModuleType) -> None:
    """리드 상세 조회 API가 정상 동작하는지 검증한다."""
    mock_repo = MagicMock()
    mock_repo.find_by_id.return_value = {"_id": "LEAD-2026-00001", "lead_name": "홍길동"}

    with patch.object(leads_mod, "_get_repo", return_value=mock_repo):
        response = test_client.get("/api/v1/leads/LEAD-2026-00001")

    assert response.status_code == 200
    assert response.json()["lead_name"] == "홍길동"


def test_리드_상세_조회_없음(test_client: TestClient, leads_mod: ModuleType) -> None:
    """존재하지 않는 리드 조회 시 404를 반환하는지 검증한다."""
    mock_repo = MagicMock()
    mock_repo.find_by_id.return_value = None

    with patch.object(leads_mod, "_get_repo", return_value=mock_repo):
        response = test_client.get("/api/v1/leads/LEAD-9999-00001")

    assert response.status_code == 404


def test_리드_수정(test_client: TestClient, leads_mod: ModuleType) -> None:
    """리드 수정 API가 초안 상태에서 동작하는지 검증한다."""
    mock_repo = MagicMock()
    mock_repo.find_by_id.return_value = {"_id": "LEAD-2026-00001", "docstatus": 0}
    mock_repo.update_by_id.return_value = True

    with patch.object(leads_mod, "_get_repo", return_value=mock_repo):
        response = test_client.put(
            "/api/v1/leads/LEAD-2026-00001",
            json={
                "lead_name": "김철수",
            },
        )

    assert response.status_code == 200


def test_리드_삭제(test_client: TestClient, leads_mod: ModuleType) -> None:
    """리드 삭제 API가 초안 상태에서 동작하는지 검증한다."""
    mock_repo = MagicMock()
    mock_repo.find_by_id.return_value = {"_id": "LEAD-2026-00001", "docstatus": 0}
    mock_repo.delete_by_id.return_value = True

    with patch.object(leads_mod, "_get_repo", return_value=mock_repo):
        response = test_client.delete("/api/v1/leads/LEAD-2026-00001")

    assert response.status_code == 204


def test_리드_목록은_워크벤치_요약과_상태배지를_반환한다(
    test_client: TestClient, leads_mod: ModuleType
) -> None:
    """리드 목록이 상태/점수/활동 기반 워크벤치 요약을 반환한다."""
    mock_repo = MagicMock()
    mock_repo.find_many.return_value = [
        {
            "_id": "LEAD-2026-00001",
            "lead_name": "AI 제조 리드",
            "status": "qualified",
            "lead_score": 92,
            "source": "웹사이트",
            "interested_item": "스마트팩토리",
        },
        {
            "_id": "LEAD-2026-00002",
            "lead_name": "재참여 대상",
            "status": "lost",
            "lead_score": 18,
            "source": "전시회",
            "interested_item": "MES",
        },
    ]
    activity_repo = MagicMock()
    activity_repo.find_many.side_effect = [
        [
            {
                "party_type": "lead",
                "party": "LEAD-2026-00001",
                "activity_type": "meeting",
                "activity_date": "2026-04-09",
            }
        ],
        [],
    ]
    opportunity_repo = MagicMock()
    opportunity_repo.find_many.side_effect = [[], []]

    with (
        patch.object(leads_mod, "_get_repo", return_value=mock_repo),
        patch.object(leads_mod, "_get_activity_repo", return_value=activity_repo),
        patch.object(leads_mod, "_get_opportunity_repo", return_value=opportunity_repo),
    ):
        response = test_client.get("/api/v1/leads?status=qualified")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["summary"]["qualified_count"] == 1
    assert data["summary"]["high_score_count"] == 1
    assert data["summary"]["stale_follow_up_count"] == 0
    row = data["data"][0]
    assert row["status_badge"] == "qualified_hot"
    assert row["recommended_action"] == "convert_to_opportunity"
    assert row["score_summary"]["score_grade"] == "hot"
    assert row["activity_summary"]["activity_count"] == 1


def test_리드_요약은_활동점수와_전환가이드를_반환한다(
    test_client: TestClient, leads_mod: ModuleType
) -> None:
    """리드 요약이 활동/점수/전환 컨텍스트를 보여준다."""
    mock_repo = MagicMock()
    mock_repo.find_by_id.return_value = {
        "_id": "LEAD-2026-00001",
        "lead_name": "전환 준비 리드",
        "status": "qualified",
        "lead_score": 76,
        "source": "파트너 추천",
        "interested_item": "현장서비스",
        "created_at": datetime(2026, 4, 1, 9, 0, tzinfo=UTC),
    }
    activity_repo = MagicMock()
    activity_repo.find_many.return_value = [
        {
            "party_type": "lead",
            "party": "LEAD-2026-00001",
            "activity_type": "call",
            "activity_date": "2026-04-05",
            "assigned_to": "sales-owner",
        },
        {
            "party_type": "lead",
            "party": "LEAD-2026-00001",
            "activity_type": "meeting",
            "activity_date": "2026-04-08",
            "assigned_to": "sales-owner",
        },
    ]
    opportunity_repo = MagicMock()
    opportunity_repo.find_many.return_value = [
        {"_id": "OPP-2026-00001", "lead_ref": "LEAD-2026-00001"}
    ]

    with (
        patch.object(leads_mod, "_get_repo", return_value=mock_repo),
        patch.object(leads_mod, "_get_activity_repo", return_value=activity_repo),
        patch.object(leads_mod, "_get_opportunity_repo", return_value=opportunity_repo),
    ):
        response = test_client.get("/api/v1/leads/LEAD-2026-00001/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["status_badge"] == "qualified_ready"
    assert data["recommended_action"] == "convert_to_opportunity"
    assert data["score_summary"]["lead_score"] == 76.0
    assert data["score_summary"]["score_grade"] == "warm"
    assert data["activity_summary"]["activity_count"] == 2
    assert data["activity_summary"]["latest_activity_type"] == "meeting"
    assert data["conversion_summary"]["linked_opportunity_count"] == 1
    assert data["conversion_summary"]["can_convert_to_opportunity"] is True


def test_리드_이메일중복은_생성할_수_없다(test_client: TestClient, leads_mod: ModuleType) -> None:
    """같은 이메일 리드는 중복 생성할 수 없다."""
    mock_repo = MagicMock()
    mock_repo.find_many.return_value = [{"_id": "LEAD-2026-00001", "email": "dup@test.com"}]

    with patch.object(leads_mod, "_get_repo", return_value=mock_repo):
        response = test_client.post(
            "/api/v1/leads",
            json={
                "lead_name": "중복 리드",
                "company_name": "중복 회사",
                "email": "dup@test.com",
            },
        )

    assert response.status_code == 409
