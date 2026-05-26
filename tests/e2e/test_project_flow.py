"""E2E: 프로젝트 플로우 — Project → Task → Timesheet."""

from __future__ import annotations

import httpx
import pytest

from tests.e2e.helpers.api_client import HEADERS

pytestmark = pytest.mark.e2e


class TestProjectFlow:
    """프로젝트 모듈의 전체 사용자 시나리오를 검증한다."""

    def test_프로젝트_CRUD(self, projects_client: httpx.Client) -> None:
        """Project 생성 → 조회 → 수정 → 삭제."""
        resp = projects_client.post(
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
        resp = projects_client.get(f"/api/v1/projects/{proj_id}")
        assert resp.status_code == 200
        assert resp.json()["project_name"] == "E2E 테스트 프로젝트"

        # 상태 변경
        resp = projects_client.put(
            f"/api/v1/projects/{proj_id}",
            json={
                "status": "in_progress",
                "percent_complete": 30.0,
            },
        )
        assert resp.status_code == 200

        # 목록
        resp = projects_client.get("/api/v1/projects")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

        # 삭제
        resp = projects_client.delete(f"/api/v1/projects/{proj_id}")
        assert resp.status_code == 204

    def test_마일스톤_워크벤치와_완료후_청구상태를_조회한다(
        self, projects_client: httpx.Client
    ) -> None:
        """마일스톤 목록/상세가 청구 준비 상태와 액션을 제공해야 한다."""
        resp = projects_client.post(
            "/api/v1/projects",
            json={
                "project_name": "마일스톤 워크벤치 프로젝트",
                "customer": "CUST-MILESTONE-001",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        project_id = resp.json()["id"]

        resp = projects_client.post(
            "/api/v1/milestones/",
            json={
                "milestone_name": "UAT 완료",
                "project": project_id,
                "due_date": "2026-04-01",
                "completion_criteria": "고객 승인서 업로드",
                "billing_amount": "2500000",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        milestone_id = resp.json()["milestone_id"]

        resp = projects_client.post(f"/api/v1/milestones/{milestone_id}/complete", headers=HEADERS)
        assert resp.status_code == 200
        billing_id = resp.json()["billing_id"]
        assert billing_id.startswith("PBL-")

        resp = projects_client.get(
            f"/api/v1/milestones/?project={project_id}&billing_status=ready_to_invoice",
            headers=HEADERS,
        )
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["summary"]["ready_to_invoice_count"] == 1
        assert payload["summary"]["total_billing_amount"] == 2500000.0
        assert payload["data"][0]["_id"] == milestone_id
        assert payload["data"][0]["status_badge"] == "completed_ready_to_invoice"
        assert payload["data"][0]["billing_summary"]["billing_status"] == "ready_to_invoice"
        assert payload["data"][0]["available_actions"] == ["view", "open_billing"]

        resp = projects_client.get(f"/api/v1/milestones/{milestone_id}", headers=HEADERS)
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["status_badge"] == "completed_ready_to_invoice"
        assert detail["billing_summary"]["billing_id"] == billing_id
        assert detail["available_actions"] == ["view", "open_billing"]

    def test_작업_CRUD(self, projects_client: httpx.Client) -> None:
        """Task 생성 → 조회 → 수정 → 삭제."""
        # 프로젝트 생성
        resp = projects_client.post(
            "/api/v1/projects",
            json={
                "project_name": "Task 테스트 프로젝트",
            },
        )
        proj_id = resp.json()["id"]

        # 작업 생성
        resp = projects_client.post(
            "/api/v1/tasks",
            json={
                "subject": "E2E API 구현",
                "project_ref": proj_id,
                "assigned_to": "EMP-E2E-TASK-001",
                "priority": "high",
                "expected_time": 8.0,
            },
        )
        assert resp.status_code == 201
        task_id = resp.json()["id"]

        # 조회
        resp = projects_client.get(f"/api/v1/tasks/{task_id}")
        assert resp.status_code == 200
        assert resp.json()["subject"] == "E2E API 구현"

        # 상태 변경
        resp = projects_client.put(
            f"/api/v1/tasks/{task_id}",
            json={
                "status": "working",
                "actual_time": 4.0,
            },
        )
        assert resp.status_code == 200

        # 삭제
        resp = projects_client.delete(f"/api/v1/tasks/{task_id}")
        assert resp.status_code == 204

    def test_작업_상태전이와_타임시트참조_삭제차단(
        self,
        hr_client: httpx.Client,
        projects_client: httpx.Client,
    ) -> None:
        """작업은 담당자/실적/검토 단계를 거쳐야 하고 제출 타임시트가 있으면 삭제할 수 없어야 한다."""
        resp = hr_client.post(
            "/api/v1/employees",
            json={
                "employee_name": "작업 흐름 담당자",
                "department": "개발팀",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        employee_id = resp.json().get("id") or resp.json()["_id"]

        resp = projects_client.post(
            "/api/v1/projects",
            json={"project_name": "작업 상태전이 프로젝트"},
            headers=HEADERS,
        )
        assert resp.status_code == 201
        project_id = resp.json()["id"]

        resp = projects_client.post(
            "/api/v1/tasks",
            json={
                "subject": "검토 전환 작업",
                "project_ref": project_id,
                "assigned_to": employee_id,
                "start_date": "2026-04-01",
                "end_date": "2026-04-02",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        task_id = resp.json()["id"]

        resp = projects_client.put(
            f"/api/v1/tasks/{task_id}",
            json={"status": "working"},
            headers=HEADERS,
        )
        assert resp.status_code == 200

        resp = projects_client.put(
            f"/api/v1/tasks/{task_id}",
            json={"status": "pending_review"},
            headers=HEADERS,
        )
        assert resp.status_code == 422
        assert resp.json()["error"] == "ERR-PRJ-013"

        resp = projects_client.put(
            f"/api/v1/tasks/{task_id}",
            json={"actual_time": 5.0},
            headers=HEADERS,
        )
        assert resp.status_code == 200

        resp = projects_client.put(
            f"/api/v1/tasks/{task_id}",
            json={"status": "pending_review"},
            headers=HEADERS,
        )
        assert resp.status_code == 200

        resp = projects_client.put(
            f"/api/v1/tasks/{task_id}",
            json={"status": "completed"},
            headers=HEADERS,
        )
        assert resp.status_code == 200

        resp = projects_client.post(
            "/api/v1/timesheets",
            json={
                "employee_id": employee_id,
                "employee_name": "작업 흐름 담당자",
                "start_date": "2026-04-01",
                "end_date": "2026-04-05",
                "total_hours": 5.0,
                "time_logs": [
                    {
                        "date": "2026-04-03",
                        "project_ref": project_id,
                        "task_ref": task_id,
                        "hours": 5.0,
                        "activity_type": "개발",
                    }
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        timesheet_id = resp.json()["id"]

        resp = projects_client.post(
            f"/api/v1/timesheets/{timesheet_id}/submit",
            headers=HEADERS,
        )
        assert resp.status_code == 200

        resp = projects_client.delete(f"/api/v1/tasks/{task_id}", headers=HEADERS)
        assert resp.status_code == 422
        assert resp.json()["error"] == "ERR-PRJ-015"

    def test_타임시트_생성_제출(
        self,
        hr_client: httpx.Client,
        projects_client: httpx.Client,
    ) -> None:
        """Timesheet 생성 → 제출 → 운영 요약/급여 준비 → 인보이싱."""
        # 직원 생성
        resp = hr_client.post(
            "/api/v1/employees",
            json={
                "employee_name": "타임시트 테스트 직원",
                "department": "개발팀",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        emp_id = resp.json().get("id") or resp.json()["_id"]

        # 프로젝트 생성
        resp = projects_client.post(
            "/api/v1/projects",
            json={
                "project_name": "타임시트 프로젝트",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        proj_id = resp.json()["id"]

        resp = projects_client.post(
            "/api/v1/timesheets",
            json={
                "employee_id": emp_id,
                "employee_name": "타임시트 테스트 직원",
                "start_date": "2026-03-22",
                "end_date": "2026-03-16",
                "total_hours": 8.0,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 422
        assert resp.json()["error"] == "ERR-PRJ-016"

        # 타임시트 생성
        resp = projects_client.post(
            "/api/v1/timesheets",
            json={
                "employee_id": emp_id,
                "employee_name": "타임시트 테스트 직원",
                "start_date": "2026-03-16",
                "end_date": "2026-03-22",
                "total_hours": 40.0,
                "time_logs": [
                    {
                        "date": "2026-03-18",
                        "project_ref": proj_id,
                        "hours": 32.0,
                        "activity_type": "개발",
                    },
                    {
                        "date": "2026-03-19",
                        "project_ref": proj_id,
                        "hours": 8.0,
                        "activity_type": "코드리뷰",
                    },
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        ts_id = resp.json()["id"]

        # 조회
        resp = projects_client.get(f"/api/v1/timesheets/{ts_id}", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["total_hours"] == 40.0
        assert resp.json()["time_log_summary"]["project_refs"] == [proj_id]
        assert resp.json()["payroll_summary"]["ready_for_payroll"] is False

        # 제출
        resp = projects_client.post(f"/api/v1/timesheets/{ts_id}/submit", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["status"] == "submitted"

        resp = projects_client.get(
            f"/api/v1/timesheets?employee_id={emp_id}&project_ref={proj_id}&docstatus=1&billed=false",
            headers=HEADERS,
        )
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["total"] == 1
        assert payload["summary"]["submitted_count"] == 1
        assert payload["summary"]["payroll_ready_hours"] == 40.0
        assert payload["data"][0]["status_badge"] == "submitted_unbilled"
        assert payload["data"][0]["available_actions"] == ["create_invoice", "view"]

        resp = projects_client.get(f"/api/v1/timesheets/{ts_id}", headers=HEADERS)
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["payroll_summary"]["ready_for_payroll"] is True
        assert detail["time_log_summary"]["activity_breakdown"] == [
            {"activity_type": "개발", "hours": 32.0},
            {"activity_type": "코드리뷰", "hours": 8.0},
        ]

        resp = projects_client.post(
            f"/api/v1/timesheets/{ts_id}/invoice",
            json={"hourly_rate": 120000},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["amount"] == 4800000.0

        resp = projects_client.get(f"/api/v1/timesheets/{ts_id}", headers=HEADERS)
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["status_badge"] == "submitted_billed"
        assert detail["billing_summary"]["billing_count"] == 1
        assert detail["available_actions"] == ["view", "view_invoice"]

    def test_프로젝트_관리자_요약과_삭제제약(
        self,
        hr_client: httpx.Client,
        projects_client: httpx.Client,
    ) -> None:
        """프로젝트 관리자 연결, 목록 요약, 자식 문서 삭제 제약을 검증한다."""
        resp = hr_client.post(
            "/api/v1/employees",
            json={
                "employee_name": "프로젝트 PM",
                "department": "PMO",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        manager_id = resp.json().get("id") or resp.json()["_id"]

        resp = projects_client.post(
            "/api/v1/projects",
            json={
                "project_name": "프로젝트 요약 테스트",
                "company": "COMP-PM",
                "project_manager": manager_id,
                "budget": 15000000,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        project_id = resp.json()["id"]

        for subject in ("킥오프", "주간 점검"):
            resp = projects_client.post(
                "/api/v1/tasks",
                json={
                    "subject": subject,
                    "project_ref": project_id,
                    "assigned_to": manager_id,
                },
                headers=HEADERS,
            )
            assert resp.status_code == 201

        resp = projects_client.get(
            f"/api/v1/projects?status=open&company=COMP-PM&project_manager={manager_id}",
            headers=HEADERS,
        )
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["total"] == 1
        assert payload["summary"]["open"] == 1
        assert payload["summary"]["total_budget"] == 15000000.0
        assert payload["summary"]["average_progress"] == 0.0
        assert payload["data"][0]["project_manager_name"] == "프로젝트 PM"
        assert payload["data"][0]["task_count"] == 2

        resp = projects_client.delete(f"/api/v1/projects/{project_id}", headers=HEADERS)
        assert resp.status_code == 422
        assert resp.json()["error"] == "ERR-PRJ-011"

    def test_활동유형_워크벤치는_요약과_권장액션을_제공한다(
        self,
        hr_client: httpx.Client,
        projects_client: httpx.Client,
    ) -> None:
        """활동유형 목록/상세가 사용량과 미청구 시간 기준 운영 컨텍스트를 제공해야 한다."""
        activity_type_name = "E2E 활동유형 개발"

        resp = hr_client.post(
            "/api/v1/employees",
            json={
                "employee_name": "활동유형 워크벤치 담당자",
                "department": "PMO",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        employee_id = resp.json().get("id") or resp.json()["_id"]

        resp = projects_client.post(
            "/api/v1/projects",
            json={"project_name": "활동유형 워크벤치 프로젝트"},
            headers=HEADERS,
        )
        assert resp.status_code == 201
        project_id = resp.json()["id"]

        resp = projects_client.post(
            "/api/v1/activity-types/",
            json={
                "activity_type": activity_type_name,
                "costing_rate": 70000,
                "billing_rate": 120000,
                "is_active": True,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        activity_type_id = resp.json()["id"]

        resp = projects_client.post(
            "/api/v1/timesheets",
            json={
                "employee_id": employee_id,
                "employee_name": "활동유형 워크벤치 담당자",
                "start_date": "2026-04-01",
                "end_date": "2026-04-05",
                "total_hours": 8.0,
                "time_logs": [
                    {
                        "date": "2026-04-03",
                        "project_ref": project_id,
                        "hours": 8.0,
                        "activity_type": activity_type_name,
                    }
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        timesheet_id = resp.json()["id"]

        resp = projects_client.post(
            f"/api/v1/timesheets/{timesheet_id}/submit",
            headers=HEADERS,
        )
        assert resp.status_code == 200

        resp = projects_client.get("/api/v1/activity-types/", headers=HEADERS)
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["summary"]["active_count"] == 1
        assert payload["summary"]["in_use_count"] == 1
        assert payload["summary"]["unbilled_hours"] == 8.0
        assert payload["data"][0]["status_badge"] == "active_in_use"
        assert payload["data"][0]["recommended_action"] == "review_unbilled_timesheets"

        resp = projects_client.get(
            f"/api/v1/activity-types/{activity_type_id}",
            headers=HEADERS,
        )
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["usage_summary"] == {
            "timesheet_count": 1,
            "submitted_timesheet_count": 1,
            "active_project_count": 1,
            "total_logged_hours": 8.0,
            "unbilled_hours": 8.0,
            "last_used_date": "2026-04-03",
        }
        assert detail["rate_summary"]["margin_per_hour"] == 50000.0
        assert detail["available_actions"] == ["edit", "open_timesheets", "deactivate"]

        resp = projects_client.delete(
            f"/api/v1/activity-types/{activity_type_id}",
            headers=HEADERS,
        )
        assert resp.status_code == 422
        assert resp.json()["error"] == "ERR-PRJ-010"
