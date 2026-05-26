"""직급(Designation) API 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

from oneerp_core.repository import Repository

_BASE_URL = "/api/v1/designations"


def test_직급_생성_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """직급 생성 API가 rank_order/is_active 필드와 함께 동작하는지 검증한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="DESG-2026-00001")
    response = test_client.post(
        f"{_BASE_URL}",
        json={
            "title": "과장",
            "description": "중간 관리자",
            "rank_order": 20,
            "is_active": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "_id" in data
    assert data["rank_order"] == 20
    assert data["is_active"] is True


def test_직급_목록_조회(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """직급 목록 API가 페이지네이션과 함께 동작하는지 검증한다."""
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(
        return_value=iter(
            [
                {
                    "_id": "DESG-001",
                    "title": "사원",
                    "rank_order": 10,
                    "is_active": True,
                }
            ]
        ),
    )
    mock_collection.find.return_value = mock_cursor
    mock_collection.count_documents.return_value = 1
    response = test_client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["data"][0]["rank_order"] == 10


def test_직급_조회_미존재_404(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """존재하지 않는 직급 조회 시 404를 반환하는지 검증한다."""
    mock_collection.find_one.return_value = None
    response = test_client.get(f"{_BASE_URL}/NOT-EXIST")
    assert response.status_code == 404


def test_직급_체계_조회는_재직인원만_집계한다(monkeypatch, test_client: MagicMock) -> None:
    """직급 체계 조회는 재직 중(active) 직원만 employee_count로 집계한다."""

    def fake_find_many(self: Repository, query=None, *, sort=None, skip=0, limit=20):
        if self._collection_name == "designations":
            return [
                {
                    "_id": "DESG-002",
                    "title": "팀장",
                    "rank_order": 30,
                    "is_active": True,
                },
                {
                    "_id": "DESG-001",
                    "title": "사원",
                    "rank_order": 10,
                    "is_active": True,
                },
            ]
        if self._collection_name == "employees":
            return [
                {"_id": "EMP-001", "designation": "팀장", "status": "active"},
                {"_id": "EMP-002", "designation": "팀장", "status": "left"},
                {"_id": "EMP-003", "designation": "사원", "status": "active"},
            ]
        return []

    monkeypatch.setattr(Repository, "find_many", fake_find_many)

    response = test_client.get(f"{_BASE_URL}/hierarchy")

    assert response.status_code == 200
    data = response.json()["data"]
    assert [item["title"] for item in data] == ["사원", "팀장"]
    assert data[0]["employee_count"] == 1
    assert data[1]["employee_count"] == 1


def test_직급_삭제는_재직자만_차단한다(monkeypatch, test_client: MagicMock) -> None:
    """퇴사자만 남은 직급은 삭제할 수 있고 재직자 직급만 삭제를 막는다."""

    def fake_find_by_id(self: Repository, doc_id: str):
        if self._collection_name == "designations":
            return {"_id": doc_id, "title": "팀장", "rank_order": 30, "is_active": True}
        return None

    def fake_count(self: Repository, query=None):
        if self._collection_name == "employees":
            if query == {"designation": "팀장", "status": "active"}:
                return 0
            return 1
        return 0

    monkeypatch.setattr(Repository, "find_by_id", fake_find_by_id)
    monkeypatch.setattr(Repository, "count", fake_count)

    response = test_client.delete(f"{_BASE_URL}/DESG-2026-00001")

    assert response.status_code == 204
