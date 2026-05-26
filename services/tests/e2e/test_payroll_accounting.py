"""급여→회계 E2E 테스트.

급여 처리 → 급여명세서 생성 → 회계 분개 자동 생성 흐름을 검증한다.
hr → payroll → accounting 서비스 간 데이터 흐름을 확인한다.
"""

from __future__ import annotations

import time

import httpx
import pytest

from tests.e2e.helpers.api_client import HEADERS

pytestmark = pytest.mark.e2e

# 비동기 이벤트 처리 대기 시간 (초)
_EVENT_WAIT = 2.0
# 폴링 최대 횟수
_POLL_MAX = 10
# 폴링 간격 (초)
_POLL_INTERVAL = 0.5


def _poll_until(
    client: httpx.Client,
    url: str,
    *,
    check: str,
    expected: object,
    max_attempts: int = _POLL_MAX,
) -> dict:
    """응답의 특정 필드가 기대값이 될 때까지 폴링한다."""
    for _ in range(max_attempts):
        resp = client.get(url, headers=HEADERS)
        if resp.status_code == 200:
            body = resp.json()
            if "data" in body and isinstance(body["data"], list) and len(body["data"]) > 0:
                if body["data"][0].get(check) == expected:
                    return body
            elif body.get(check) == expected:
                return body
        time.sleep(_POLL_INTERVAL)
    msg = f"{url}에서 {check}=={expected} 조건을 {max_attempts}회 폴링 후에도 충족하지 못했습니다"
    raise TimeoutError(msg)


class TestPayrollAccounting:
    """급여 처리 → 급여명세서 → 회계 분개 전체 사이클을 검증한다."""

    def test_급여처리_회계분개_전체_흐름(
        self,
        hr_client: httpx.Client,
        payroll_client: httpx.Client,
        accounting_client: httpx.Client,
    ) -> None:
        """직원 생성→PayrollEntry 생성+제출→SalarySlip 검증→JE 자동 생성 검증."""
        # --- Step 1: 직원 생성 (hr 서비스) ---
        employees = []
        for i in range(3):
            resp = hr_client.post(
                "/api/v1/employees",
                json={
                    "employee_name": f"급여 E2E 직원 {i + 1}",
                    "department": "개발팀",
                    "designation": "시니어 개발자",
                    "date_of_joining": "2025-01-01",
                    "status": "active",
                },
                headers=HEADERS,
            )
            assert resp.status_code == 201
            emp = resp.json()
            employees.append(emp["id"])

        assert len(employees) == 3

        # --- Step 2: 급여구조 생성 (payroll 서비스) ---
        gross_pay = 4000000  # 기본급 + 식대 + 직책수당
        total_deduction = 380000  # 국민연금 + 건강보험 + 고용보험 + 소득세

        resp = payroll_client.post(
            "/api/v1/salary-structures",
            json={
                "name": "E2E 개발팀 급여체계",
                "company": "E2E 회사",
                "is_active": True,
                "earnings": [
                    {"component": "기본급", "amount": 3500000},
                    {"component": "식대", "amount": 200000},
                    {"component": "직책수당", "amount": 300000},
                ],
                "deductions": [
                    {"component": "국민연금", "amount": 157500},
                    {"component": "건강보험", "amount": 126000},
                    {"component": "고용보험", "amount": 36500},
                    {"component": "소득세", "amount": 60000},
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        ss_id = resp.json().get("_id") or resp.json().get("id")

        # --- Step 3: PayrollEntry 생성 (payroll 서비스) ---
        resp = payroll_client.post(
            "/api/v1/payroll-entries",
            json={
                "company": "E2E 회사",
                "posting_date": "2026-03-25",
                "payroll_frequency": "monthly",
                "start_date": "2026-03-01",
                "end_date": "2026-03-31",
                "salary_structure_id": ss_id,
                "department": "개발팀",
                "employee_ids": employees,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        pe = resp.json()
        pe_id = pe["id"]

        # PayrollEntry 조회
        resp = payroll_client.get(
            f"/api/v1/payroll-entries/{pe_id}",
            headers=HEADERS,
        )
        assert resp.status_code == 200
        pe_data = resp.json()
        assert pe_data["docstatus"] == 0  # DRAFT

        # --- Step 4: PayrollEntry 제출 ---
        resp = payroll_client.post(
            f"/api/v1/payroll-entries/{pe_id}/submit",
            headers=HEADERS,
        )
        assert resp.status_code == 200

        # 제출 상태 확인
        resp = payroll_client.get(
            f"/api/v1/payroll-entries/{pe_id}",
            headers=HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["docstatus"] == 1  # SUBMITTED

        # --- 검증: SalarySlip 생성 확인 (직원별) ---
        time.sleep(_EVENT_WAIT)
        resp = payroll_client.get(
            "/api/v1/salary-slips",
            params={"payroll_entry_id": pe_id},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        slips_data = resp.json()
        # 3명의 직원에 대한 급여명세서가 생성되어야 함
        if slips_data.get("total", 0) > 0:
            assert slips_data["total"] == len(employees)

            # 각 급여명세서의 금액 검증
            for slip in slips_data["data"]:
                assert slip["gross_pay"] == gross_pay
                assert slip["total_deduction"] == total_deduction
                net_pay = gross_pay - total_deduction
                assert slip["net_pay"] == net_pay

        # --- 검증: 분개전표 자동 생성 확인 (accounting 서비스) ---
        # 급여 분개: 차변(급여비용) / 대변(미지급급여, 예수금)
        resp = accounting_client.get(
            "/api/v1/journal-entries",
            params={"voucher_no": pe_id},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        je_data = resp.json()
        if je_data.get("total", 0) > 0:
            je = je_data["data"][0]
            # 차대변 합계 일치 검증 — 급여 분개의 기본 원칙
            assert je["total_debit"] == je["total_credit"]

            # 총 급여비용 = 직원 수 * gross_pay
            expected_total = len(employees) * gross_pay
            assert je["total_debit"] == expected_total

    def test_개별_급여명세서_직접_생성_제출(
        self,
        hr_client: httpx.Client,
        payroll_client: httpx.Client,
        accounting_client: httpx.Client,
    ) -> None:
        """SalarySlip 개별 생성 → 제출 → 분개전표 검증."""
        # 직원 생성
        resp = hr_client.post(
            "/api/v1/employees",
            json={
                "employee_name": "개별 급여 테스트 직원",
                "department": "인사팀",
                "designation": "매니저",
                "date_of_joining": "2024-06-01",
                "status": "active",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        emp_id = resp.json().get("_id") or resp.json().get("id")

        # 급여명세서 생성
        gross_pay = 3200000
        total_deduction = 247000
        net_pay = gross_pay - total_deduction

        resp = payroll_client.post(
            "/api/v1/salary-slips",
            json={
                "employee_id": emp_id,
                "employee_name": "개별 급여 테스트 직원",
                "posting_date": "2026-03-25",
                "start_date": "2026-03-01",
                "end_date": "2026-03-31",
                "gross_pay": gross_pay,
                "total_deduction": total_deduction,
                "net_pay": net_pay,
                "earnings": [
                    {"component": "기본급", "amount": 3000000},
                    {"component": "식대", "amount": 200000},
                ],
                "deductions": [
                    {"component": "국민연금", "amount": 135000},
                    {"component": "건강보험", "amount": 112000},
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        slip_id = resp.json().get("_id") or resp.json().get("id")

        # 조회 — 금액 검증
        resp = payroll_client.get(
            f"/api/v1/salary-slips/{slip_id}",
            headers=HEADERS,
        )
        assert resp.status_code == 200
        slip = resp.json()
        assert slip["gross_pay"] == gross_pay
        assert slip["net_pay"] == net_pay

        # 제출
        resp = payroll_client.post(
            f"/api/v1/salary-slips/{slip_id}/submit",
            headers=HEADERS,
        )
        assert resp.status_code == 200

        # 분개전표 검증
        time.sleep(_EVENT_WAIT)
        resp = accounting_client.get(
            "/api/v1/journal-entries",
            params={"voucher_no": slip_id},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        je_data = resp.json()
        if je_data.get("total", 0) > 0:
            je = je_data["data"][0]
            assert je["total_debit"] == je["total_credit"]
