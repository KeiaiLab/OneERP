"""코스트센터(CostCenter) CRUD 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from oneerp_accounting_app.main import app

client = TestClient(app)
client.headers.update(
    {
        "X-Tenant-Id": "test-tenant",
        "X-User-Sub": "test-user",
        "X-User-Roles": "admin",
        "X-User-Permissions": "*:*",
        "X-User-Tier": "super_admin",
    }
)


@patch("oneerp_accounting_app.routes.cost_centers._get_repo")
@patch("oneerp_accounting_app.routes.cost_centers.generate_name", return_value="CC-2026-00001")
def test_코스트센터_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """POST /api/v1/cost-centers -- 정상 생성 시 201과 _id를 반환한다."""
    repo = MagicMock()
    repo.find_many.return_value = []
    mock_repo.return_value = repo
    response = client.post(
        "/api/v1/cost-centers",
        json={
            "cost_center_name": "영업부",
            "company": "테스트 회사",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "CC-2026-00001"
    assert data["_id"] == "CC-2026-00001"


@patch("oneerp_accounting_app.routes.cost_centers._get_repo")
def test_코스트센터_목록_조회(mock_repo: MagicMock) -> None:
    """GET /api/v1/cost-centers -- 목록 응답을 확인한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "CC-001", "cost_center_name": "영업부"}]
    mock_repo.return_value = repo
    response = client.get("/api/v1/cost-centers")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


@patch("oneerp_accounting_app.routes.cost_centers._get_repo")
def test_코스트센터_상세_조회_미존재_404(mock_repo: MagicMock) -> None:
    """GET /api/v1/cost-centers/{doc_id} -- 없는 코스트센터는 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/cost-centers/NOT-EXIST")
    assert response.status_code == 404


@patch("oneerp_accounting_app.routes.cost_centers._get_repo")
def test_코스트센터_트리_조회(mock_repo: MagicMock) -> None:
    """GET /api/v1/cost-centers/tree -- 계층 구조와 요약을 반환한다."""
    repo = MagicMock()
    repo.find_many.return_value = [
        {
            "_id": "CC-001",
            "cost_center_name": "본사",
            "company": "테스트 회사",
            "is_group": True,
            "parent_cost_center": None,
        },
        {
            "_id": "CC-002",
            "cost_center_name": "영업부",
            "company": "테스트 회사",
            "is_group": False,
            "parent_cost_center": "CC-001",
        },
    ]
    mock_repo.return_value = repo

    response = client.get("/api/v1/cost-centers/tree")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert payload["summary"]["group_count"] == 1
    assert payload["summary"]["leaf_count"] == 1
    assert payload["summary"]["company_counts"]["테스트 회사"] == 2
    assert payload["data"][0]["_id"] == "CC-001"
    assert payload["data"][0]["children"][0]["_id"] == "CC-002"


@patch("oneerp_accounting_app.routes.cost_centers._get_budget_repo", create=True)
@patch("oneerp_accounting_app.routes.cost_centers._get_journal_entry_repo", create=True)
@patch("oneerp_accounting_app.routes.cost_centers._get_repo")
def test_코스트센터_삭제는_하위센터가_있으면_차단(
    mock_repo: MagicMock,
    mock_journal_repo: MagicMock,
    mock_budget_repo: MagicMock,
) -> None:
    """DELETE /api/v1/cost-centers/{doc_id} -- 하위 코스트센터가 있으면 삭제를 차단한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "CC-001",
        "cost_center_name": "본사",
        "docstatus": 0,
    }
    repo.count.side_effect = [1]
    mock_repo.return_value = repo
    mock_journal_repo.return_value = MagicMock()
    mock_budget_repo.return_value = MagicMock()

    response = client.delete("/api/v1/cost-centers/CC-001")

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-ACCT-031"


@patch("oneerp_accounting_app.routes.cost_centers._get_budget_repo", create=True)
@patch("oneerp_accounting_app.routes.cost_centers._get_journal_entry_repo", create=True)
@patch("oneerp_accounting_app.routes.cost_centers._get_repo")
def test_코스트센터_삭제는_분개나_예산에서_사용중이면_차단(
    mock_repo: MagicMock,
    mock_journal_repo: MagicMock,
    mock_budget_repo: MagicMock,
) -> None:
    """DELETE /api/v1/cost-centers/{doc_id} -- 분개/예산 참조가 있으면 삭제를 차단한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "CC-002",
        "cost_center_name": "영업부",
        "docstatus": 0,
    }
    repo.count.return_value = 0
    mock_repo.return_value = repo
    journal_repo = MagicMock()
    journal_repo.count.return_value = 1
    mock_journal_repo.return_value = journal_repo
    budget_repo = MagicMock()
    budget_repo.count.return_value = 0
    mock_budget_repo.return_value = budget_repo

    response = client.delete("/api/v1/cost-centers/CC-002")

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-ACCT-032"
