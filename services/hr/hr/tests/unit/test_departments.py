"""부서(Department) API 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import oneerp_hr_app.routes.departments as department_routes

_BASE_URL = "/api/v1/departments"


def test_부서_생성시_public_id를_함께_반환한다(
    monkeypatch,
    test_client,
) -> None:
    """커스텀 부서 라우터가 생성 응답에 id와 _id를 함께 제공해야 한다."""
    dept_repo = MagicMock()
    monkeypatch.setattr(department_routes, "_get_department_repo", lambda tenant_id: dept_repo)
    monkeypatch.setattr(
        department_routes,
        "generate_name",
        lambda prefix, **kwargs: "DEPT-2026-00001",
    )

    response = test_client.post(
        _BASE_URL,
        json={
            "department_name": "플랫폼본부",
            "company": "OneERP",
            "is_group": True,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "DEPT-2026-00001"
    assert data["_id"] == "DEPT-2026-00001"
    assert data["department_name"] == "플랫폼본부"


def test_부서_조직도_트리가_하위부서와_인원수를_반환한다(
    monkeypatch,
    test_client,
) -> None:
    """조직도 조회 시 계층 구조와 부서별 인원 수를 함께 반환해야 한다."""
    dept_repo = MagicMock()
    emp_repo = MagicMock()
    monkeypatch.setattr(department_routes, "_get_department_repo", lambda tenant_id: dept_repo)
    monkeypatch.setattr(department_routes, "_get_employee_repo", lambda tenant_id: emp_repo)
    dept_repo.find_many.return_value = [
        {
            "_id": "DEPT-001",
            "department_name": "본사",
            "parent_department": None,
            "company": "OneERP",
            "is_group": True,
        },
        {
            "_id": "DEPT-002",
            "department_name": "개발팀",
            "parent_department": "DEPT-001",
            "company": "OneERP",
            "is_group": False,
        },
        {
            "_id": "DEPT-003",
            "department_name": "영업팀",
            "parent_department": "DEPT-001",
            "company": "OneERP",
            "is_group": False,
        },
    ]
    emp_repo.find_many.return_value = [
        {"_id": "EMP-001", "department": "개발팀"},
        {"_id": "EMP-002", "department": "개발팀"},
        {"_id": "EMP-003", "department": "영업팀"},
    ]

    response = test_client.get(f"{_BASE_URL}/tree")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    root = payload["data"][0]
    assert root["department_name"] == "본사"
    assert root["child_count"] == 2
    child_counts = {child["department_name"]: child["employee_count"] for child in root["children"]}
    assert child_counts == {"개발팀": 2, "영업팀": 1}


def test_하위부서가_있으면_삭제할_수_없다(
    monkeypatch,
    test_client,
) -> None:
    """하위 부서가 남아 있으면 삭제를 차단해야 한다."""
    dept_repo = MagicMock()
    emp_repo = MagicMock()
    monkeypatch.setattr(department_routes, "_get_department_repo", lambda tenant_id: dept_repo)
    monkeypatch.setattr(department_routes, "_get_employee_repo", lambda tenant_id: emp_repo)
    dept_repo.find_by_id.return_value = {
        "_id": "DEPT-001",
        "department_name": "본사",
        "company": "OneERP",
        "is_group": True,
    }
    dept_repo.count.return_value = 2
    emp_repo.count.return_value = 0

    response = test_client.delete(f"{_BASE_URL}/DEPT-001")

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-HR-033"
    assert "하위 부서가 있어 삭제할 수 없습니다" in response.json()["detail"]
    dept_repo.delete_by_id.assert_not_called()


def test_존재하지_않는_상위부서는_생성할_수_없다(
    monkeypatch,
    test_client,
) -> None:
    """상위 부서는 반드시 기존 부서여야 한다."""
    dept_repo = MagicMock()
    monkeypatch.setattr(department_routes, "_get_department_repo", lambda tenant_id: dept_repo)
    monkeypatch.setattr(
        department_routes,
        "generate_name",
        lambda prefix, **kwargs: "DEPT-2026-00009",
    )
    dept_repo.find_by_id.return_value = None

    response = test_client.post(
        _BASE_URL,
        json={
            "department_name": "플랫폼운영팀",
            "company": "OneERP",
            "parent_department": "DEPT-404",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-HR-044"
    dept_repo.insert.assert_not_called()


def test_조직도_순환이_생기도록_수정할_수_없다(
    monkeypatch,
    test_client,
) -> None:
    """자기 자신 또는 하위 부서를 상위 부서로 지정하는 순환 구조를 막아야 한다."""
    dept_repo = MagicMock()
    monkeypatch.setattr(department_routes, "_get_department_repo", lambda tenant_id: dept_repo)
    dept_repo.find_by_id.side_effect = lambda doc_id: {
        "DEPT-001": {
            "_id": "DEPT-001",
            "department_name": "본사",
            "parent_department": None,
            "company": "OneERP",
        },
        "DEPT-002": {
            "_id": "DEPT-002",
            "department_name": "개발팀",
            "parent_department": "DEPT-001",
            "company": "OneERP",
        },
    }.get(doc_id)
    dept_repo.find_many.return_value = [
        {
            "_id": "DEPT-001",
            "department_name": "본사",
            "parent_department": None,
            "company": "OneERP",
        },
        {
            "_id": "DEPT-002",
            "department_name": "개발팀",
            "parent_department": "DEPT-001",
            "company": "OneERP",
        },
    ]

    response = test_client.put(
        f"{_BASE_URL}/DEPT-001",
        json={"parent_department": "DEPT-002"},
    )

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-HR-045"
    dept_repo.update_by_id.assert_not_called()


def test_직원이_배정된_부서는_삭제할_수_없다(
    monkeypatch,
    test_client,
) -> None:
    """재직 중인 직원이 배정된 부서를 삭제하면 조직 데이터가 깨진다."""
    dept_repo = MagicMock()
    emp_repo = MagicMock()
    monkeypatch.setattr(department_routes, "_get_department_repo", lambda tenant_id: dept_repo)
    monkeypatch.setattr(department_routes, "_get_employee_repo", lambda tenant_id: emp_repo)
    dept_repo.find_by_id.return_value = {
        "_id": "DEPT-010",
        "department_name": "플랫폼팀",
        "company": "OneERP",
        "parent_department": None,
    }
    dept_repo.count.return_value = 0
    emp_repo.count.return_value = 1

    response = test_client.delete(f"{_BASE_URL}/DEPT-010")

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-HR-046"
    dept_repo.delete_by_id.assert_not_called()
