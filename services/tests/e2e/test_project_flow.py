"""E2E: 프로젝트 플로우 — Project → Task → Timesheet."""

from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.e2e


class TestProjectFlow:
    """프로젝트 모듈의 전체 사용자 시나리오를 검증한다."""

    def test_프로젝트_CRUD(self, gateway_client: httpx.Client) -> None:
        """Project 생성 → 조회 → 수정 → 삭제."""
        resp = gateway_client.post(
            "/api/v1/projects",
            json={
                "project_name": "E2E 테스트 프로젝트",
                "expected_start_date": "2026-04-01",
                "expected_end_date": "2026-06-30",
                "company": "E2E 회사",
            },
        )
        assert resp.status_code == 201
        proj_id = resp.json()["id"]

        # 조회
        resp = gateway_client.get(f"/api/v1/projects/{proj_id}")
        assert resp.status_code == 200
        assert resp.json()["project_name"] == "E2E 테스트 프로젝트"

        # 상태 변경
        resp = gateway_client.put(
            f"/api/v1/projects/{proj_id}",
            json={
                "status": "in_progress",
                "percent_complete": 30.0,
            },
        )
        assert resp.status_code == 200

        # 목록
        resp = gateway_client.get("/api/v1/projects")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

        # 삭제
        resp = gateway_client.delete(f"/api/v1/projects/{proj_id}")
        assert resp.status_code == 204

    def test_작업_CRUD(self, gateway_client: httpx.Client) -> None:
        """Task 생성 → 조회 → 수정 → 삭제."""
        # 프로젝트 생성
        resp = gateway_client.post(
            "/api/v1/projects",
            json={
                "project_name": "Task 테스트 프로젝트",
            },
        )
        proj_id = resp.json()["id"]

        # 작업 생성
        resp = gateway_client.post(
            "/api/v1/tasks",
            json={
                "subject": "E2E API 구현",
                "project_ref": proj_id,
                "priority": "high",
                "expected_time": 8.0,
            },
        )
        assert resp.status_code == 201
        task_id = resp.json()["id"]

        # 조회
        resp = gateway_client.get(f"/api/v1/tasks/{task_id}")
        assert resp.status_code == 200
        assert resp.json()["subject"] == "E2E API 구현"

        # 상태 변경
        resp = gateway_client.put(
            f"/api/v1/tasks/{task_id}",
            json={
                "status": "working",
                "actual_time": 4.0,
            },
        )
        assert resp.status_code == 200

        # 삭제
        resp = gateway_client.delete(f"/api/v1/tasks/{task_id}")
        assert resp.status_code == 204

    def test_타임시트_생성_제출(self, gateway_client: httpx.Client) -> None:
        """Timesheet 생성 → 제출."""
        # 직원 생성
        resp = gateway_client.post(
            "/api/v1/employees",
            json={
                "employee_name": "타임시트 테스트 직원",
                "department": "개발팀",
            },
        )
        emp_id = resp.json()["id"]

        # 프로젝트 생성
        resp = gateway_client.post(
            "/api/v1/projects",
            json={
                "project_name": "타임시트 프로젝트",
            },
        )
        proj_id = resp.json()["id"]

        # 타임시트 생성
        resp = gateway_client.post(
            "/api/v1/timesheets",
            json={
                "employee_id": emp_id,
                "employee_name": "타임시트 테스트 직원",
                "start_date": "2026-03-16",
                "end_date": "2026-03-22",
                "total_hours": 40.0,
                "time_logs": [
                    {"project_ref": proj_id, "hours": 8.0, "activity_type": "개발"},
                    {"project_ref": proj_id, "hours": 8.0, "activity_type": "코드리뷰"},
                ],
            },
        )
        assert resp.status_code == 201
        ts_id = resp.json()["id"]

        # 조회
        resp = gateway_client.get(f"/api/v1/timesheets/{ts_id}")
        assert resp.status_code == 200
        assert resp.json()["total_hours"] == 40.0

        # 제출
        resp = gateway_client.post(f"/api/v1/timesheets/{ts_id}/submit")
        assert resp.status_code == 200
