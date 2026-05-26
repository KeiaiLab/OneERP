"""E2E: HR 플로우 — Department → Employee → LeaveApplication → Attendance."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import pytest

from tests.e2e.helpers.api_client import HEADERS

pytestmark = pytest.mark.e2e


class TestHRFlow:
    """HR 모듈의 전체 사용자 시나리오를 검증한다."""

    def test_부서_CRUD(self, hr_client: httpx.Client) -> None:
        """부서 생성 → 조회 → 수정 → 삭제."""
        resp = hr_client.post(
            "/api/v1/departments",
            json={
                "department_name": "E2E 개발팀",
                "company": "E2E 회사",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        dept_id = resp.json()["id"]

        resp = hr_client.get(f"/api/v1/departments/{dept_id}", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["department_name"] == "E2E 개발팀"

        resp = hr_client.put(
            f"/api/v1/departments/{dept_id}",
            json={
                "department_name": "E2E 수정 개발팀",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 200

        resp = hr_client.delete(f"/api/v1/departments/{dept_id}", headers=HEADERS)
        assert resp.status_code == 204

    def test_부서_조직도_검증과_직원배정_삭제제약(self, hr_client: httpx.Client) -> None:
        """상위 부서 검증, 조직도 순환 차단, 직원 배정 부서 삭제 차단을 확인한다."""
        invalid_parent = hr_client.post(
            "/api/v1/departments",
            json={
                "department_name": "E2E 유령팀",
                "company": "E2E 회사",
                "parent_department": "DEPT-404",
            },
            headers=HEADERS,
        )
        assert invalid_parent.status_code == 422
        assert invalid_parent.json()["error"] == "ERR-HR-044"

        parent_resp = hr_client.post(
            "/api/v1/departments",
            json={
                "department_name": "E2E 본사",
                "company": "E2E 회사",
                "is_group": True,
            },
            headers=HEADERS,
        )
        assert parent_resp.status_code == 201
        parent_id = parent_resp.json()["id"]

        child_resp = hr_client.post(
            "/api/v1/departments",
            json={
                "department_name": "E2E 플랫폼팀",
                "company": "E2E 회사",
                "parent_department": parent_id,
            },
            headers=HEADERS,
        )
        assert child_resp.status_code == 201
        child_id = child_resp.json()["id"]

        cycle_resp = hr_client.put(
            f"/api/v1/departments/{parent_id}",
            json={"parent_department": child_id},
            headers=HEADERS,
        )
        assert cycle_resp.status_code == 422
        assert cycle_resp.json()["error"] == "ERR-HR-045"

        employee_resp = hr_client.post(
            "/api/v1/employees",
            json={
                "employee_name": "E2E 부서직원",
                "department": "E2E 플랫폼팀",
                "designation": "사원",
                "date_of_joining": "2026-01-02",
                "employment_type": "REGULAR",
                "company": "E2E 회사",
            },
            headers=HEADERS,
        )
        assert employee_resp.status_code == 201
        employee_id = employee_resp.json().get("id") or employee_resp.json()["_id"]

        tree_resp = hr_client.get("/api/v1/departments/tree", headers=HEADERS)
        assert tree_resp.status_code == 200
        root = next(item for item in tree_resp.json()["data"] if item["id"] == parent_id)
        child = next(item for item in root["children"] if item["id"] == child_id)
        assert child["employee_count"] == 1

        blocked_resp = hr_client.delete(f"/api/v1/departments/{child_id}", headers=HEADERS)
        assert blocked_resp.status_code == 422
        assert blocked_resp.json()["error"] == "ERR-HR-046"

        delete_employee = hr_client.delete(f"/api/v1/employees/{employee_id}", headers=HEADERS)
        assert delete_employee.status_code == 204

        delete_child = hr_client.delete(f"/api/v1/departments/{child_id}", headers=HEADERS)
        assert delete_child.status_code == 204

        delete_parent = hr_client.delete(f"/api/v1/departments/{parent_id}", headers=HEADERS)
        assert delete_parent.status_code == 204

    def test_직급_체계는_재직인원만_집계하고_퇴사후_삭제된다(self, hr_client: httpx.Client) -> None:
        """직급 체계는 active 직원만 집계하고, 퇴사 처리 후에는 직급 삭제가 가능해야 한다."""
        designation_resp = hr_client.post(
            "/api/v1/designations",
            json={
                "title": "E2E 팀장",
                "description": "조직장 직급",
                "rank_order": 30,
                "is_active": True,
            },
            headers=HEADERS,
        )
        assert designation_resp.status_code == 201
        designation_id = designation_resp.json()["id"]

        active_employee_resp = hr_client.post(
            "/api/v1/employees",
            json={
                "employee_name": "재직 직급 사용자",
                "department": "플랫폼팀",
                "designation": "E2E 팀장",
                "date_of_joining": "2026-01-01",
                "employment_type": "REGULAR",
            },
            headers=HEADERS,
        )
        assert active_employee_resp.status_code == 201
        active_employee_id = active_employee_resp.json()["id"]

        left_employee_resp = hr_client.post(
            "/api/v1/employees",
            json={
                "employee_name": "퇴사 직급 사용자",
                "department": "플랫폼팀",
                "designation": "E2E 팀장",
                "date_of_joining": "2025-01-01",
                "employment_type": "REGULAR",
            },
            headers=HEADERS,
        )
        assert left_employee_resp.status_code == 201
        left_employee_id = left_employee_resp.json()["id"]

        leave_employee = hr_client.put(
            f"/api/v1/employees/{left_employee_id}",
            json={"status": "left"},
            headers=HEADERS,
        )
        assert leave_employee.status_code == 200

        hierarchy_resp = hr_client.get("/api/v1/designations/hierarchy", headers=HEADERS)
        assert hierarchy_resp.status_code == 200
        designation_rows = [
            row for row in hierarchy_resp.json()["data"] if row["id"] == designation_id
        ]
        assert designation_rows[0]["employee_count"] == 1

        blocked_delete = hr_client.delete(
            f"/api/v1/designations/{designation_id}",
            headers=HEADERS,
        )
        assert blocked_delete.status_code == 422
        assert blocked_delete.json()["error"] == "ERR-HR-034"

        active_leave = hr_client.put(
            f"/api/v1/employees/{active_employee_id}",
            json={"status": "left"},
            headers=HEADERS,
        )
        assert active_leave.status_code == 200

        delete_designation = hr_client.delete(
            f"/api/v1/designations/{designation_id}",
            headers=HEADERS,
        )
        assert delete_designation.status_code == 204

        delete_active_employee = hr_client.delete(
            f"/api/v1/employees/{active_employee_id}",
            headers=HEADERS,
        )
        assert delete_active_employee.status_code == 204

        delete_left_employee = hr_client.delete(
            f"/api/v1/employees/{left_employee_id}",
            headers=HEADERS,
        )
        assert delete_left_employee.status_code == 204

    def test_직원_CRUD(self, hr_client: httpx.Client) -> None:
        """직원 생성 → 조회 → 수정 → 삭제."""
        resp = hr_client.post(
            "/api/v1/employees",
            json={
                "employee_name": "E2E 김테스트",
                "department": "개발팀",
                "designation": "시니어 개발자",
                "date_of_joining": "2026-01-01",
                "date_of_birth": "1991-04-05",
                "employment_type": "REGULAR",
                "reports_to": "",
                "email": "test@e2e.com",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        emp_id = resp.json()["id"]

        resp = hr_client.get(f"/api/v1/employees/{emp_id}", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["employee_name"] == "E2E 김테스트"
        assert resp.json()["date_of_birth"].split("T", 1)[0] == "1991-04-05"
        assert resp.json()["employment_type"] == "REGULAR"

        # 목록
        resp = hr_client.get("/api/v1/employees", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

        resp = hr_client.delete(f"/api/v1/employees/{emp_id}", headers=HEADERS)
        assert resp.status_code == 204

    def test_인사발령_워크벤치는_변경영향과_급여연계가이드를_반환한다(
        self,
        hr_client: httpx.Client,
    ) -> None:
        """인사발령은 초안→제출→취소 흐름과 직원 마스터 반영을 함께 제공해야 한다."""
        today = datetime.now(tz=UTC).date()
        department_from = f"HR-E2E-영업-{today:%Y%m%d}"
        department_to = f"HR-E2E-기획-{today:%Y%m%d}"
        designation_from = f"HR-E2E-사원-{today:%Y%m%d}"
        designation_to = f"HR-E2E-대리-{today:%Y%m%d}"

        resp = hr_client.post(
            "/api/v1/departments",
            json={"department_name": department_from, "company": "E2E 회사"},
            headers=HEADERS,
        )
        assert resp.status_code == 201
        from_department_id = resp.json().get("id") or resp.json()["_id"]

        resp = hr_client.post(
            "/api/v1/departments",
            json={"department_name": department_to, "company": "E2E 회사"},
            headers=HEADERS,
        )
        assert resp.status_code == 201
        to_department_id = resp.json().get("id") or resp.json()["_id"]

        resp = hr_client.post(
            "/api/v1/designations",
            json={"title": designation_from, "rank_order": 10},
            headers=HEADERS,
        )
        assert resp.status_code == 201
        from_designation_id = resp.json().get("id") or resp.json()["_id"]

        resp = hr_client.post(
            "/api/v1/designations",
            json={"title": designation_to, "rank_order": 20},
            headers=HEADERS,
        )
        assert resp.status_code == 201
        to_designation_id = resp.json().get("id") or resp.json()["_id"]

        employee_resp = hr_client.post(
            "/api/v1/employees",
            json={
                "employee_name": f"인사발령 테스트 직원 {today:%Y%m%d}",
                "department": department_from,
                "designation": designation_from,
                "date_of_joining": "2026-01-02",
                "employment_type": "REGULAR",
                "company": "E2E 회사",
            },
            headers=HEADERS,
        )
        assert employee_resp.status_code == 201
        employee_id = employee_resp.json()["id"]

        create_resp = hr_client.post(
            "/api/v1/employee-transfers",
            json={
                "employee": employee_id,
                "transfer_date": today.isoformat(),
                "to_department": department_to,
                "to_designation": designation_to,
                "reason": "조직개편",
            },
            headers=HEADERS,
        )
        assert create_resp.status_code == 201
        transfer_id = create_resp.json()["id"]

        listing_resp = hr_client.get(
            f"/api/v1/employee-transfers?employee={employee_id}",
            headers=HEADERS,
        )
        assert listing_resp.status_code == 200
        listing = listing_resp.json()
        assert listing["total"] == 1
        assert listing["summary"]["draft_count"] == 1
        assert listing["data"][0]["status_badge"] == "draft_ready"
        assert listing["data"][0]["recommended_action"] == "submit_transfer"

        submit_resp = hr_client.post(
            f"/api/v1/employee-transfers/{transfer_id}/submit",
            headers=HEADERS,
        )
        assert submit_resp.status_code == 200

        detail_resp = hr_client.get(
            f"/api/v1/employee-transfers/{transfer_id}/summary",
            headers=HEADERS,
        )
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["status_badge"] == "submitted_dual_change"
        assert detail["change_summary"]["change_scope"] == "department_and_designation"
        assert detail["impact_summary"]["current_department"] == department_to
        assert detail["impact_summary"]["current_designation"] == designation_to
        assert detail["sync_summary"]["employee_update_event_count"] >= 1
        assert detail["recommended_action"] == "verify_payroll_sync"
        assert detail["available_actions"] == [
            "open_employee_profile",
            "verify_payroll_sync",
            "cancel",
        ]

        employee_after_submit = hr_client.get(f"/api/v1/employees/{employee_id}", headers=HEADERS)
        assert employee_after_submit.status_code == 200
        assert employee_after_submit.json()["department"] == department_to
        assert employee_after_submit.json()["designation"] == designation_to

        cancel_resp = hr_client.post(
            f"/api/v1/employee-transfers/{transfer_id}/cancel",
            headers=HEADERS,
        )
        assert cancel_resp.status_code == 200
        assert cancel_resp.json()["status_badge"] == "cancelled"

        employee_after_cancel = hr_client.get(f"/api/v1/employees/{employee_id}", headers=HEADERS)
        assert employee_after_cancel.status_code == 200
        assert employee_after_cancel.json()["department"] == department_from
        assert employee_after_cancel.json()["designation"] == designation_from

        assert (
            hr_client.delete(f"/api/v1/employees/{employee_id}", headers=HEADERS).status_code == 204
        )
        assert (
            hr_client.delete(f"/api/v1/departments/{to_department_id}", headers=HEADERS).status_code
            == 204
        )
        assert (
            hr_client.delete(
                f"/api/v1/departments/{from_department_id}", headers=HEADERS
            ).status_code
            == 204
        )
        assert (
            hr_client.delete(
                f"/api/v1/designations/{to_designation_id}", headers=HEADERS
            ).status_code
            == 204
        )
        assert (
            hr_client.delete(
                f"/api/v1/designations/{from_designation_id}", headers=HEADERS
            ).status_code
            == 204
        )

    def test_직원_디렉터리와_보고라인_삭제제약(self, hr_client: httpx.Client) -> None:
        """보고라인이 있는 직원은 삭제할 수 없고 디렉터리에서 관리자명이 보여야 한다."""
        manager_resp = hr_client.post(
            "/api/v1/employees",
            json={
                "employee_name": "E2E 김팀장",
                "department": "플랫폼팀",
                "designation": "팀장",
                "date_of_joining": "2024-01-01",
                "employment_type": "REGULAR",
            },
            headers=HEADERS,
        )
        assert manager_resp.status_code == 201
        manager_id = manager_resp.json()["id"]

        subordinate_resp = hr_client.post(
            "/api/v1/employees",
            json={
                "employee_name": "E2E 박사원",
                "department": "플랫폼팀",
                "designation": "사원",
                "date_of_joining": "2026-02-01",
                "employment_type": "INTERN",
                "reports_to": manager_id,
            },
            headers=HEADERS,
        )
        assert subordinate_resp.status_code == 201
        subordinate_id = subordinate_resp.json()["id"]

        directory_resp = hr_client.get("/api/v1/employees/directory?status=active", headers=HEADERS)
        assert directory_resp.status_code == 200
        directory = directory_resp.json()
        manager = next(item for item in directory["data"] if item["id"] == manager_id)
        subordinate = next(item for item in directory["data"] if item["id"] == subordinate_id)
        assert manager["direct_report_count"] == 1
        assert subordinate["manager_name"] == "E2E 김팀장"

        blocked_delete = hr_client.delete(f"/api/v1/employees/{manager_id}", headers=HEADERS)
        assert blocked_delete.status_code == 422
        assert blocked_delete.json()["error"] == "ERR-HR-043"

        clear_manager = hr_client.put(
            f"/api/v1/employees/{subordinate_id}",
            json={"reports_to": ""},
            headers=HEADERS,
        )
        assert clear_manager.status_code == 200

        left_manager = hr_client.put(
            f"/api/v1/employees/{manager_id}",
            json={"status": "left"},
            headers=HEADERS,
        )
        assert left_manager.status_code == 200

        delete_manager = hr_client.delete(f"/api/v1/employees/{manager_id}", headers=HEADERS)
        assert delete_manager.status_code == 204
        delete_subordinate = hr_client.delete(
            f"/api/v1/employees/{subordinate_id}", headers=HEADERS
        )
        assert delete_subordinate.status_code == 204

    def test_휴가신청_승인_반려(self, hr_client: httpx.Client) -> None:
        """휴가신청 생성 → 승인 / 반려 워크플로우."""
        annual_leave_type = "E2E 승인 연차"
        sick_leave_type = "E2E 반려 병가"

        # 직원 생성
        resp = hr_client.post(
            "/api/v1/employees",
            json={
                "employee_name": "휴가 테스트 직원",
                "department": "인사팀",
            },
            headers=HEADERS,
        )
        emp_id = resp.json()["id"]

        for leave_type in (annual_leave_type, sick_leave_type):
            resp = hr_client.post(
                "/api/v1/leave-types",
                json={
                    "leave_type_name": leave_type,
                    "max_leaves_allowed": 10,
                    "is_paid": True,
                    "is_active": True,
                },
                headers=HEADERS,
            )
            assert resp.status_code == 201

        resp = hr_client.post(
            "/api/v1/leave-balances",
            json={
                "employee": emp_id,
                "leave_type": annual_leave_type,
                "total_allocated": 10,
                "total_used": 0,
                "balance": 10,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201

        # 휴가신청 생성
        resp = hr_client.post(
            "/api/v1/leave-applications",
            json={
                "employee_id": emp_id,
                "employee_name": "휴가 테스트 직원",
                "leave_type": annual_leave_type,
                "from_date": "2026-04-01",
                "to_date": "2026-04-03",
                "total_days": 3,
                "reason": "개인 사유",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        leave_id = resp.json()["id"]

        # 조회
        resp = hr_client.get(f"/api/v1/leave-applications/{leave_id}", headers=HEADERS)
        assert resp.status_code == 200

        # 승인
        resp = hr_client.post(f"/api/v1/leave-applications/{leave_id}/approve", headers=HEADERS)
        assert resp.status_code == 200

        # 두 번째 휴가 — 반려 테스트
        resp = hr_client.post(
            "/api/v1/leave-applications",
            json={
                "employee_id": emp_id,
                "employee_name": "휴가 테스트 직원",
                "leave_type": sick_leave_type,
                "from_date": "2026-05-01",
                "to_date": "2026-05-02",
                "total_days": 2,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        leave_id2 = resp.json()["id"]

        resp = hr_client.post(f"/api/v1/leave-applications/{leave_id2}/reject", headers=HEADERS)
        assert resp.status_code == 200

    def test_휴가신청_워크벤치는_승인현황과_잔액리스크를_보여준다(
        self,
        hr_client: httpx.Client,
    ) -> None:
        """휴가신청 목록/상세는 승인 현황과 잔액 리스크를 한 화면에서 보여줘야 한다."""

        leave_type_name = "E2E 신청 워크벤치 연차"

        leave_type_resp = hr_client.post(
            "/api/v1/leave-types",
            json={
                "leave_type_name": leave_type_name,
                "max_leaves_allowed": 15,
                "is_paid": True,
                "is_active": True,
            },
            headers=HEADERS,
        )
        assert leave_type_resp.status_code == 201

        employee_resp = hr_client.post(
            "/api/v1/employees",
            json={
                "employee_name": "휴가 워크벤치 직원",
                "department": "인사팀",
                "designation": "대리",
                "date_of_joining": "2025-01-01",
            },
            headers=HEADERS,
        )
        assert employee_resp.status_code == 201
        employee_id = employee_resp.json().get("id") or employee_resp.json()["_id"]

        balance_resp = hr_client.post(
            "/api/v1/leave-balances",
            json={
                "employee": employee_id,
                "leave_type": leave_type_name,
                "total_allocated": 8,
                "total_used": 2,
                "balance": 6,
            },
            headers=HEADERS,
        )
        assert balance_resp.status_code == 201

        approved_resp = hr_client.post(
            "/api/v1/leave-applications",
            json={
                "employee_id": employee_id,
                "employee_name": "휴가 워크벤치 직원",
                "leave_type": leave_type_name,
                "from_date": "2026-07-01",
                "to_date": "2026-07-03",
                "total_days": 3,
                "reason": "여름 휴가",
            },
            headers=HEADERS,
        )
        assert approved_resp.status_code == 201
        approved_id = approved_resp.json()["id"]

        approve_call = hr_client.post(
            f"/api/v1/leave-applications/{approved_id}/approve",
            headers=HEADERS,
        )
        assert approve_call.status_code == 200

        open_resp = hr_client.post(
            "/api/v1/leave-applications",
            json={
                "employee_id": employee_id,
                "employee_name": "휴가 워크벤치 직원",
                "leave_type": leave_type_name,
                "from_date": "2026-08-10",
                "to_date": "2026-08-13",
                "total_days": 4,
                "reason": "잔여 검증",
            },
            headers=HEADERS,
        )
        assert open_resp.status_code == 201
        open_id = open_resp.json()["id"]

        listing = hr_client.get(
            "/api/v1/leave-applications",
            params={"employee_id": employee_id, "leave_type": leave_type_name, "page_size": 100},
            headers=HEADERS,
        )
        assert listing.status_code == 200
        listing_body = listing.json()
        assert listing_body["total"] >= 2
        assert listing_body["summary"]["open_count"] >= 1
        assert listing_body["summary"]["approved_count"] >= 1
        assert listing_body["summary"]["insufficient_balance_count"] >= 1
        assert listing_body["summary"]["employee_count"] >= 1

        open_row = next(row for row in listing_body["data"] if row["id"] == open_id)
        approved_row = next(row for row in listing_body["data"] if row["id"] == approved_id)
        assert open_row["status_badge"] == "pending_balance_review"
        assert open_row["recommended_action"] == "adjust_leave_balance"
        assert open_row["leave_balance_summary"]["remaining_days"] == 3.0
        assert open_row["leave_balance_summary"]["remaining_after_request"] == -1.0
        assert open_row["available_actions"] == ["approve", "reject", "delete"]
        assert approved_row["status_badge"] == "approved_deducted"

        detail = hr_client.get(f"/api/v1/leave-applications/{open_id}/summary", headers=HEADERS)
        assert detail.status_code == 200
        detail_body = detail.json()
        assert detail_body["status_badge"] == "pending_balance_review"
        assert detail_body["period_summary"] == {
            "from_date": "2026-08-10",
            "to_date": "2026-08-13",
            "total_days": 4.0,
            "is_single_day": False,
        }
        assert detail_body["leave_balance_summary"] == {
            "allocated_days": 8.0,
            "used_days": 5.0,
            "remaining_days": 3.0,
            "requested_days": 4.0,
            "remaining_after_request": -1.0,
            "has_sufficient_balance": False,
        }

    def test_휴가유형_워크벤치는_정책과_신청현황_삭제제약을_보여준다(
        self,
        hr_client: httpx.Client,
    ) -> None:
        """휴가유형 목록/상세는 정책·잔액·신청 현황을 보여주고 사용 이력 삭제를 막아야 한다."""
        leave_type_name = "E2E 유형 워크벤치 연차"

        create_leave_type = hr_client.post(
            "/api/v1/leave-types",
            json={
                "leave_type_name": leave_type_name,
                "max_leaves_allowed": 15,
                "is_carry_forward": True,
                "is_paid": True,
            },
            headers=HEADERS,
        )
        assert create_leave_type.status_code == 201
        leave_type_id = create_leave_type.json()["id"]

        create_policy = hr_client.post(
            "/api/v1/leave-policies",
            json={
                "policy_name": "E2E 유형 워크벤치 연차 정책",
                "leave_type_id": leave_type_id,
                "annual_allocation": 15,
                "carry_forward": True,
                "max_carry_forward_days": 5,
            },
            headers=HEADERS,
        )
        assert create_policy.status_code == 201

        employee_resp = hr_client.post(
            "/api/v1/employees",
            json={
                "employee_name": "휴가유형 워크벤치 직원",
                "department": "인사팀",
                "designation": "대리",
                "date_of_joining": "2025-03-01",
            },
            headers=HEADERS,
        )
        assert employee_resp.status_code == 201
        employee_id = employee_resp.json().get("id") or employee_resp.json()["_id"]

        create_balance = hr_client.post(
            "/api/v1/leave-balances",
            json={
                "employee": employee_id,
                "leave_type": leave_type_name,
                "total_allocated": 15,
                "total_used": 3,
                "balance": 12,
            },
            headers=HEADERS,
        )
        assert create_balance.status_code == 201

        create_application = hr_client.post(
            "/api/v1/leave-applications",
            json={
                "employee_id": employee_id,
                "employee_name": "휴가유형 워크벤치 직원",
                "leave_type": leave_type_name,
                "from_date": "2026-06-01",
                "to_date": "2026-06-02",
                "total_days": 2,
                "reason": "휴가 워크벤치 검증",
            },
            headers=HEADERS,
        )
        assert create_application.status_code == 201

        listing = hr_client.get("/api/v1/leave-types", headers=HEADERS)
        assert listing.status_code == 200
        listing_body = listing.json()
        assert listing_body["summary"]["request_backlog_count"] >= 1
        leave_type_row = next(row for row in listing_body["data"] if row["id"] == leave_type_id)
        assert leave_type_row["status_badge"] == "request_backlog"
        assert leave_type_row["summary"]["policy_count"] == 1
        assert leave_type_row["summary"]["balance_employee_count"] == 1
        assert leave_type_row["summary"]["open_application_count"] == 1

        detail = hr_client.get(f"/api/v1/leave-types/{leave_type_id}", headers=HEADERS)
        assert detail.status_code == 200
        detail_body = detail.json()
        assert detail_body["recommended_action"] == "review_open_requests"
        assert "open_leave_applications" in detail_body["available_actions"]

        summary = hr_client.get(f"/api/v1/leave-types/{leave_type_id}/summary", headers=HEADERS)
        assert summary.status_code == 200
        assert summary.json()["summary"]["max_carry_forward_days"] == 5.0

        delete_resp = hr_client.delete(f"/api/v1/leave-types/{leave_type_id}", headers=HEADERS)
        assert delete_resp.status_code == 422
        assert delete_resp.json()["error"] == "ERR-HR-050"

    def test_휴가잔액_워크벤치는_만료위험과_이월가이드를_반환한다(
        self,
        hr_client: httpx.Client,
    ) -> None:
        """휴가잔액 목록/상세는 만료 위험, 이월 예상치, 운영 액션을 함께 보여줘야 한다."""
        today = datetime.now(tz=UTC).date()
        fiscal_year = str(today.year)
        expiry_date = today + timedelta(days=21)
        leave_type_name = "E2E 잔액 워크벤치 연차"

        employee_resp = hr_client.post(
            "/api/v1/employees",
            json={
                "employee_name": "휴가잔액 워크벤치 직원",
                "department": "인사팀",
                "designation": "사원",
                "date_of_joining": "2021-04-01",
            },
            headers=HEADERS,
        )
        assert employee_resp.status_code == 201
        employee_id = employee_resp.json().get("id") or employee_resp.json().get("_id")

        leave_type_resp = hr_client.post(
            "/api/v1/leave-types",
            json={
                "leave_type_name": leave_type_name,
                "max_leaves_allowed": 15,
                "is_carry_forward": True,
                "is_paid": True,
            },
            headers=HEADERS,
        )
        assert leave_type_resp.status_code == 201
        leave_type_id = leave_type_resp.json().get("id") or leave_type_resp.json().get("_id")

        policy_resp = hr_client.post(
            "/api/v1/leave-policies",
            json={
                "policy_name": "E2E 잔액 워크벤치 이월 정책",
                "leave_type_id": leave_type_id,
                "annual_allocation": 15,
                "carry_forward": True,
                "max_carry_forward_days": 5,
            },
            headers=HEADERS,
        )
        assert policy_resp.status_code == 201

        balance_resp = hr_client.post(
            "/api/v1/leave-balances",
            json={
                "employee": employee_id,
                "leave_type": leave_type_name,
                "fiscal_year": fiscal_year,
                "expiry_date": expiry_date.isoformat(),
                "total_allocated": 15,
                "total_used": 4,
                "balance": 11,
            },
            headers=HEADERS,
        )
        assert balance_resp.status_code == 201
        balance_id = balance_resp.json().get("id") or balance_resp.json().get("_id")

        approved_resp = hr_client.post(
            "/api/v1/leave-applications",
            json={
                "employee_id": employee_id,
                "employee_name": "휴가잔액 워크벤치 직원",
                "leave_type": leave_type_name,
                "from_date": today.isoformat(),
                "to_date": (today + timedelta(days=1)).isoformat(),
                "total_days": 2,
                "reason": "승인 이력",
            },
            headers=HEADERS,
        )
        assert approved_resp.status_code == 201
        approved_id = approved_resp.json()["id"]

        approve_call = hr_client.post(
            f"/api/v1/leave-applications/{approved_id}/approve",
            headers=HEADERS,
        )
        assert approve_call.status_code == 200

        open_resp = hr_client.post(
            "/api/v1/leave-applications",
            json={
                "employee_id": employee_id,
                "employee_name": "휴가잔액 워크벤치 직원",
                "leave_type": leave_type_name,
                "from_date": (today + timedelta(days=30)).isoformat(),
                "to_date": (today + timedelta(days=31)).isoformat(),
                "total_days": 2,
                "reason": "승인 대기",
            },
            headers=HEADERS,
        )
        assert open_resp.status_code == 201

        listing = hr_client.get(
            f"/api/v1/leave-balances?employee_id={employee_id}&fiscal_year={fiscal_year}",
            headers=HEADERS,
        )
        assert listing.status_code == 200
        listing_body = listing.json()
        assert listing_body["total"] == 1
        assert listing_body["summary"]["employee_count"] == 1
        assert listing_body["summary"]["expiring_soon_count"] == 1
        assert listing_body["summary"]["carry_forward_ready_count"] == 1

        row = listing_body["data"][0]
        assert row["status_badge"] == "expiring_soon"
        assert row["recommended_action"] == "review_expiry"
        assert row["summary"]["approved_application_count"] == 1
        assert row["summary"]["open_application_count"] == 1
        assert row["summary"]["expected_carry_forward_days"] == 5.0
        assert "run_carry_forward" in row["available_actions"]

        detail = hr_client.get(f"/api/v1/leave-balances/{balance_id}/summary", headers=HEADERS)
        assert detail.status_code == 200
        detail_body = detail.json()
        assert detail_body["status_badge"] == "expiring_soon"
        assert detail_body["carry_forward_summary"]["carry_forward_cap_days"] == 5.0
        assert detail_body["carry_forward_summary"]["expected_carry_forward_days"] == 5.0
        assert detail_body["carry_forward_summary"]["expires_in_days"] <= 21

    def test_근태_등록_조회(self, hr_client: httpx.Client) -> None:
        """근태 생성 → 조회."""
        # 직원 생성
        resp = hr_client.post(
            "/api/v1/employees",
            json={
                "employee_name": "근태 테스트 직원",
                "department": "개발팀",
            },
            headers=HEADERS,
        )
        emp_id = resp.json()["id"]

        # 근태 등록
        resp = hr_client.post(
            "/api/v1/attendances",
            json={
                "employee_id": emp_id,
                "employee_name": "근태 테스트 직원",
                "attendance_date": "2026-03-17",
                "status": "present",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        att_id = resp.json()["id"]

        # 조회
        resp = hr_client.get(f"/api/v1/attendances/{att_id}", headers=HEADERS)
        assert resp.status_code == 200

        # 목록
        resp = hr_client.get("/api/v1/attendances", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_근태_모바일체크인과_워크벤치_요약(self, hr_client: httpx.Client) -> None:
        """모바일 위젯 체크인은 위치 증빙을 남기고 워크벤치 요약에 반영되어야 한다."""
        missing_proof = hr_client.post(
            "/api/v1/attendances/check-in",
            json={
                "employee_id": "EMP-HR-E2E-002",
                "employee_name": "모바일 근태 직원",
                "department": "개발팀",
                "attendance_date": "2026-04-10",
                "capture_channel": "mobile_widget",
                "scheduled_start_time": "09:00",
                "scheduled_end_time": "18:00",
                "recorded_at": "2026-04-10T09:05:00",
            },
            headers=HEADERS,
        )
        assert missing_proof.status_code == 422
        assert missing_proof.json()["error"] == "ERR-HR-047"

        check_in_resp = hr_client.post(
            "/api/v1/attendances/check-in",
            json={
                "employee_id": "EMP-HR-E2E-002",
                "employee_name": "모바일 근태 직원",
                "department": "개발팀",
                "attendance_date": "2026-04-10",
                "capture_channel": "mobile_widget",
                "ip_address": "10.10.0.22",
                "gps_latitude": 37.5665,
                "gps_longitude": 126.9780,
                "scheduled_start_time": "09:00",
                "scheduled_end_time": "18:00",
                "recorded_at": "2026-04-10T09:05:00",
            },
            headers=HEADERS,
        )
        assert check_in_resp.status_code == 201
        attendance_id = check_in_resp.json()["id"]
        assert check_in_resp.json()["location_summary"]["location_status"] == "verified"

        workbench_resp = hr_client.get(
            "/api/v1/attendances?attendance_date=2026-04-10&capture_channel=mobile_widget&location_status=verified",
            headers=HEADERS,
        )
        assert workbench_resp.status_code == 200
        summary = workbench_resp.json()["summary"]
        assert summary["mobile_widget_count"] >= 1
        assert summary["location_verified_count"] >= 1
        row = next(item for item in workbench_resp.json()["data"] if item["id"] == attendance_id)
        assert row["status_badge"] == "checked_in_late"

        detail_resp = hr_client.get(f"/api/v1/attendances/{attendance_id}", headers=HEADERS)
        assert detail_resp.status_code == 200
        assert detail_resp.json()["location_summary"]["location_proof_type"] == "gps+ip"
        assert detail_resp.json()["available_actions"] == ["check_out", "view_weekly_summary"]
