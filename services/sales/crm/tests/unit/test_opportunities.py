"""기회(Opportunity) API 엔드포인트 테스트."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

if TYPE_CHECKING:
    from types import ModuleType

    from fastapi.testclient import TestClient


def test_기회_생성(test_client: TestClient, opportunities_mod: ModuleType) -> None:
    """기회 생성 API가 정상 동작하는지 검증한다."""
    mock_repo = MagicMock()
    mock_repo.insert.return_value = "OPP-2026-00001"

    with (
        patch.object(opportunities_mod, "_get_repo", return_value=mock_repo),
        patch("oneerp_crm_app.routes.opportunities.generate_name", return_value="OPP-2026-00001"),
    ):
        response = test_client.post(
            "/api/v1/opportunities",
            json={
                "lead_ref": "LEAD-2026-00001",
                "customer_id": "CUST-001",
                "expected_amount": 50000.0,
                "probability": 0.7,
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "OPP-2026-00001"


def test_기회_목록_조회(test_client: TestClient, opportunities_mod: ModuleType) -> None:
    """기회 목록 API가 정상 동작하는지 검증한다."""
    mock_repo = MagicMock()
    mock_repo.find_many.return_value = [{"_id": "OPP-2026-00001"}]
    mock_repo.count.return_value = 1

    with patch.object(opportunities_mod, "_get_repo", return_value=mock_repo):
        response = test_client.get("/api/v1/opportunities")

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_기회_제출(test_client: TestClient, opportunities_mod: ModuleType) -> None:
    """기회 제출 API가 초안 상태에서 동작하는지 검증한다."""
    mock_repo = MagicMock()
    mock_repo.find_by_id.return_value = {"_id": "OPP-2026-00001", "docstatus": 0}
    mock_repo.submit.return_value = True

    with patch.object(opportunities_mod, "_get_repo", return_value=mock_repo):
        response = test_client.post("/api/v1/opportunities/OPP-2026-00001/submit")

    assert response.status_code == 200


def test_기회_제출_비초안_거부(test_client: TestClient, opportunities_mod: ModuleType) -> None:
    """이미 제출된 기회의 재제출이 거부되는지 검증한다."""
    mock_repo = MagicMock()
    mock_repo.find_by_id.return_value = {"_id": "OPP-2026-00001", "docstatus": 1}

    with patch.object(opportunities_mod, "_get_repo", return_value=mock_repo):
        response = test_client.post("/api/v1/opportunities/OPP-2026-00001/submit")

    assert response.status_code == 400


def test_기회_삭제(test_client: TestClient, opportunities_mod: ModuleType) -> None:
    """기회 삭제 API가 초안 상태에서 동작하는지 검증한다."""
    mock_repo = MagicMock()
    mock_repo.find_by_id.return_value = {"_id": "OPP-2026-00001", "docstatus": 0}
    mock_repo.delete_by_id.return_value = True

    with patch.object(opportunities_mod, "_get_repo", return_value=mock_repo):
        response = test_client.delete("/api/v1/opportunities/OPP-2026-00001")

    assert response.status_code == 204


def test_기회_견적전환_요청_스키마(test_client: TestClient, opportunities_mod: ModuleType) -> None:
    """견적 전환 요청 바디가 Pydantic 런타임에서 검증된다."""
    service = MagicMock()
    service.convert_opportunity_to_quotation.return_value = {"quotation_id": "QTN-2026-00001"}

    with patch.object(opportunities_mod, "PipelineService", return_value=service):
        response = test_client.post(
            "/api/v1/opportunities/OPP-2026-00001/convert-to-quotation",
            json={
                "customer_id": "CUST-001",
                "items": [{"item_code": "ITEM-001", "qty": 1, "rate": 1000}],
                "valid_till": "2026-04-30",
            },
        )

    assert response.status_code == 200
    assert response.json()["quotation_id"] == "QTN-2026-00001"
    service.convert_opportunity_to_quotation.assert_called_once()
