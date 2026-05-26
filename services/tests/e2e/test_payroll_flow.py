"""E2E: 급여 플로우 — SalaryStructure → SalarySlip → SocialInsurance."""

from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.e2e


class TestPayrollFlow:
    """급여 모듈의 전체 사용자 시나리오를 검증한다."""

    def test_급여구조_CRUD(self, gateway_client: httpx.Client) -> None:
        """SalaryStructure 생성 → 조회 → 수정 → 삭제."""
        resp = gateway_client.post(
            "/api/v1/salary-structures",
            json={
                "name": "E2E 기본 급여체계",
                "company": "E2E 회사",
                "is_active": True,
                "earnings": [
                    {"component": "기본급", "amount": 3000000},
                    {"component": "식대", "amount": 200000},
                ],
                "deductions": [
                    {"component": "국민연금", "amount": 135000},
                    {"component": "건강보험", "amount": 112000},
                ],
            },
        )
        assert resp.status_code == 201
        ss_id = resp.json()["id"]

        # 조회
        resp = gateway_client.get(f"/api/v1/salary-structures/{ss_id}")
        assert resp.status_code == 200
        ss = resp.json()
        assert len(ss["earnings"]) == 2
        assert len(ss["deductions"]) == 2

        # 수정
        resp = gateway_client.put(
            f"/api/v1/salary-structures/{ss_id}",
            json={
                "name": "E2E 수정 급여체계",
            },
        )
        assert resp.status_code == 200

        # 삭제
        resp = gateway_client.delete(f"/api/v1/salary-structures/{ss_id}")
        assert resp.status_code == 204

    def test_급여명세서_생성_제출(self, gateway_client: httpx.Client) -> None:
        """SalarySlip 생성 → 제출."""
        # 직원 생성
        resp = gateway_client.post(
            "/api/v1/employees",
            json={
                "employee_name": "급여 테스트 직원",
                "department": "개발팀",
            },
        )
        emp_id = resp.json()["id"]

        # 급여명세 생성
        resp = gateway_client.post(
            "/api/v1/salary-slips",
            json={
                "employee_id": emp_id,
                "employee_name": "급여 테스트 직원",
                "posting_date": "2026-03-25",
                "start_date": "2026-03-01",
                "end_date": "2026-03-31",
                "gross_pay": 3200000,
                "total_deduction": 247000,
                "net_pay": 2953000,
                "earnings": [
                    {"component": "기본급", "amount": 3000000},
                    {"component": "식대", "amount": 200000},
                ],
                "deductions": [
                    {"component": "국민연금", "amount": 135000},
                    {"component": "건강보험", "amount": 112000},
                ],
            },
        )
        assert resp.status_code == 201
        slip_id = resp.json()["id"]

        # 조회
        resp = gateway_client.get(f"/api/v1/salary-slips/{slip_id}")
        assert resp.status_code == 200
        assert resp.json()["net_pay"] == 2953000

        # 제출
        resp = gateway_client.post(f"/api/v1/salary-slips/{slip_id}/submit")
        assert resp.status_code == 200

    def test_사대보험_CRUD(self, gateway_client: httpx.Client) -> None:
        """SocialInsurance 생성 → 조회 → 수정 → 삭제."""
        # 직원 생성
        resp = gateway_client.post(
            "/api/v1/employees",
            json={
                "employee_name": "보험 테스트 직원",
                "department": "인사팀",
            },
        )
        emp_id = resp.json()["id"]

        resp = gateway_client.post(
            "/api/v1/social-insurances",
            json={
                "employee_id": emp_id,
                "period": "2026-03",
                "national_pension": 135000,
                "health_insurance": 112000,
                "employment_insurance": 26000,
                "industrial_accident": 0,
                "total": 273000,
            },
        )
        assert resp.status_code == 201
        si_id = resp.json()["id"]

        # 조회
        resp = gateway_client.get(f"/api/v1/social-insurances/{si_id}")
        assert resp.status_code == 200
        assert resp.json()["total"] == 273000

        # 수정
        resp = gateway_client.put(
            f"/api/v1/social-insurances/{si_id}",
            json={
                "total": 280000,
            },
        )
        assert resp.status_code == 200

        # 삭제
        resp = gateway_client.delete(f"/api/v1/social-insurances/{si_id}")
        assert resp.status_code == 204
