"""E2E: HR 플로우 — Department → Employee → LeaveApplication → Attendance."""

from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.e2e


class TestHRFlow:
    """HR 모듈의 전체 사용자 시나리오를 검증한다."""

    def test_부서_CRUD(self, gateway_client: httpx.Client) -> None:
        """부서 생성 → 조회 → 수정 → 삭제."""
        resp = gateway_client.post(
            "/api/v1/departments",
            json={
                "department_name": "E2E 개발팀",
                "company": "E2E 회사",
            },
        )
        assert resp.status_code == 201
        dept_id = resp.json()["id"]

        resp = gateway_client.get(f"/api/v1/departments/{dept_id}")
        assert resp.status_code == 200
        assert resp.json()["department_name"] == "E2E 개발팀"

        resp = gateway_client.put(
            f"/api/v1/departments/{dept_id}",
            json={
                "department_name": "E2E 수정 개발팀",
            },
        )
        assert resp.status_code == 200

        resp = gateway_client.delete(f"/api/v1/departments/{dept_id}")
        assert resp.status_code == 204

    def test_직원_CRUD(self, gateway_client: httpx.Client) -> None:
        """직원 생성 → 조회 → 수정 → 삭제."""
        resp = gateway_client.post(
            "/api/v1/employees",
            json={
                "employee_name": "E2E 김테스트",
                "department": "개발팀",
                "designation": "시니어 개발자",
                "date_of_joining": "2026-01-01",
                "email": "test@e2e.com",
            },
        )
        assert resp.status_code == 201
        emp_id = resp.json()["id"]

        resp = gateway_client.get(f"/api/v1/employees/{emp_id}")
        assert resp.status_code == 200
        assert resp.json()["employee_name"] == "E2E 김테스트"

        # 목록
        resp = gateway_client.get("/api/v1/employees")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

        resp = gateway_client.delete(f"/api/v1/employees/{emp_id}")
        assert resp.status_code == 204

    def test_휴가신청_승인_반려(self, gateway_client: httpx.Client) -> None:
        """휴가신청 생성 → 승인 / 반려 워크플로우."""
        # 직원 생성
        resp = gateway_client.post(
            "/api/v1/employees",
            json={
                "employee_name": "휴가 테스트 직원",
                "department": "인사팀",
            },
        )
        emp_id = resp.json()["id"]

        # 휴가신청 생성
        resp = gateway_client.post(
            "/api/v1/leave-applications",
            json={
                "employee_id": emp_id,
                "employee_name": "휴가 테스트 직원",
                "leave_type": "연차",
                "from_date": "2026-04-01",
                "to_date": "2026-04-03",
                "total_days": 3,
                "reason": "개인 사유",
            },
        )
        assert resp.status_code == 201
        leave_id = resp.json()["id"]

        # 조회
        resp = gateway_client.get(f"/api/v1/leave-applications/{leave_id}")
        assert resp.status_code == 200

        # 승인
        resp = gateway_client.post(f"/api/v1/leave-applications/{leave_id}/approve")
        assert resp.status_code == 200

        # 두 번째 휴가 — 반려 테스트
        resp = gateway_client.post(
            "/api/v1/leave-applications",
            json={
                "employee_id": emp_id,
                "employee_name": "휴가 테스트 직원",
                "leave_type": "병가",
                "from_date": "2026-05-01",
                "to_date": "2026-05-02",
                "total_days": 2,
            },
        )
        leave_id2 = resp.json()["id"]

        resp = gateway_client.post(f"/api/v1/leave-applications/{leave_id2}/reject")
        assert resp.status_code == 200

    def test_근태_등록_조회(self, gateway_client: httpx.Client) -> None:
        """근태 생성 → 조회."""
        # 직원 생성
        resp = gateway_client.post(
            "/api/v1/employees",
            json={
                "employee_name": "근태 테스트 직원",
                "department": "개발팀",
            },
        )
        emp_id = resp.json()["id"]

        # 근태 등록
        resp = gateway_client.post(
            "/api/v1/attendances",
            json={
                "employee_id": emp_id,
                "employee_name": "근태 테스트 직원",
                "attendance_date": "2026-03-17",
                "status": "present",
            },
        )
        assert resp.status_code == 201
        att_id = resp.json()["id"]

        # 조회
        resp = gateway_client.get(f"/api/v1/attendances/{att_id}")
        assert resp.status_code == 200

        # 목록
        resp = gateway_client.get("/api/v1/attendances")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1
