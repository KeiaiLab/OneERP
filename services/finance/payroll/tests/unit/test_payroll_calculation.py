"""급여 계산 엔진 단위 테스트.

테스트 시나리오:
- 기본급 300만원 부양1인 급여 계산 (4대보험 + 소득세 검증)
- 시간외근무 수당 계산 (10시간 overtime)
- 영 급여 처리 (base_salary 0)
- 고소득 구간 (1000만원)
- 부양가족 3인 공제
- 소득세 서비스 단위 테스트
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError
from oneerp_payroll_app.services.income_tax_service import IncomeTaxService
from oneerp_payroll_app.services.insurance_rates import InsuranceRates
from oneerp_payroll_app.services.payroll_calculation_service import PayrollCalculationService

# --- 소득세 서비스 테스트 ---


class TestIncomeTaxService:
    """IncomeTaxService 단위 테스트."""

    def test_기본급_300만원_부양1인_소득세(self) -> None:
        """300만원 구간 소득세가 93,020원인지 검증한다."""
        tax = IncomeTaxService.calculate_monthly_tax(3_000_000, dependents=1)
        assert tax == 93_020

    def test_지방소득세(self) -> None:
        """지방소득세 = 소득세 x 10% 검증."""
        income_tax = 93_020
        local_tax = IncomeTaxService.calculate_local_income_tax(income_tax)
        assert local_tax == round(93_020 * 0.1)

    def test_영_급여_소득세(self) -> None:
        """급여 0원이면 소득세 0원이다."""
        tax = IncomeTaxService.calculate_monthly_tax(0, dependents=1)
        assert tax == 0.0

    def test_고소득_구간_소득세(self) -> None:
        """1000만원 구간에 높은 세율이 적용되는지 검증한다."""
        tax = IncomeTaxService.calculate_monthly_tax(10_000_000, dependents=1)
        assert tax == 904_600

    def test_부양가족_3인_공제(self) -> None:
        """부양가족 3인(본인+2인) → 25,000원 감면 검증."""
        tax_1 = IncomeTaxService.calculate_monthly_tax(3_000_000, dependents=1)
        tax_3 = IncomeTaxService.calculate_monthly_tax(3_000_000, dependents=3)
        # 추가 2인 x 12,500 = 25,000 감면
        assert tax_1 - tax_3 == 25_000

    def test_부양가족_공제_최소_0(self) -> None:
        """부양가족 공제로 세액이 음수가 되지 않는지 검증한다."""
        # 낮은 구간(106만 미만)이면 기본 세액 0이므로 공제해도 0
        tax = IncomeTaxService.calculate_monthly_tax(500_000, dependents=10)
        assert tax == 0.0

    def test_음수_급여_소득세(self) -> None:
        """음수 급여는 소득세 0원이다."""
        tax = IncomeTaxService.calculate_monthly_tax(-100_000, dependents=1)
        assert tax == 0.0


# --- 급여 계산 엔진 통합 테스트 (mock DB) ---


@pytest.fixture
def mock_db():
    """Repository와 naming을 mock하는 fixture."""
    with (
        patch(
            "oneerp_payroll_app.services.payroll_calculation_service.Repository"
        ) as mock_repo_cls,
        patch("oneerp_payroll_app.services.payroll_calculation_service.generate_name") as mock_name,
    ):
        # Repository mock 설정
        mock_payroll_repo = MagicMock()
        mock_slip_repo = MagicMock()

        call_count = 0

        def repo_factory(collection_name: str, **_kwargs):
            nonlocal call_count
            call_count += 1
            if collection_name == "payroll_entries":
                return mock_payroll_repo
            return mock_slip_repo

        mock_repo_cls.side_effect = repo_factory

        # naming mock
        slip_counter = 0

        def name_generator(_prefix, **_kwargs):
            nonlocal slip_counter
            slip_counter += 1
            return f"SLIP-2026-{slip_counter:05d}"

        mock_name.side_effect = name_generator

        yield {
            "payroll_repo": mock_payroll_repo,
            "slip_repo": mock_slip_repo,
            "name_gen": mock_name,
        }


class TestPayrollCalculationService:
    """PayrollCalculationService 단위 테스트."""

    def test_기본급_300만원_부양1인_급여계산(self, mock_db) -> None:
        """기본급 300만원, 부양가족 1인에 대한 전체 급여 계산을 검증한다."""
        base_salary = 3_000_000
        entry_data = {
            "_id": "PRLE-2026-00001",
            "payroll_date": None,
            "start_date": None,
            "end_date": None,
            "employees": [
                {
                    "employee_id": "EMP-001",
                    "employee_name": "홍길동",
                    "base_salary": base_salary,
                    "overtime_hours": 0,
                    "bonus": 0,
                    "allowances": 0,
                    "dependents": 1,
                },
            ],
        }
        mock_db["payroll_repo"].find_by_id.return_value = entry_data

        service = PayrollCalculationService(tenant_id="test-tenant")
        slip_ids = service.process_payroll("PRLE-2026-00001")

        assert len(slip_ids) == 1

        # 4대보험 검증 (기본급 기준)
        rates = InsuranceRates()
        expected_pension = round(base_salary * rates.national_pension_rate)
        expected_health = round(base_salary * rates.health_insurance_rate)
        expected_ltc = round(expected_health * rates.long_term_care_rate)
        expected_emp_ins = round(base_salary * rates.employment_insurance_rate)
        total_insurance = expected_pension + expected_health + expected_ltc + expected_emp_ins

        assert expected_pension == 135_000
        assert expected_health == 106_350
        assert expected_ltc == round(106_350 * 0.1281)  # 13,623
        assert expected_emp_ins == 27_000

        # 소득세 검증
        income_tax = IncomeTaxService.calculate_monthly_tax(base_salary, 1)
        assert income_tax == 93_020
        local_tax = IncomeTaxService.calculate_local_income_tax(income_tax)
        assert local_tax == round(93_020 * 0.1)  # 9,302

        # net_pay 검증
        total_deduction = total_insurance + income_tax + local_tax
        expected_net = base_salary - total_deduction

        # PayrollEntry 업데이트 호출 검증
        update_call = mock_db["payroll_repo"].update_by_id.call_args
        assert update_call is not None
        update_args = update_call[0]
        assert update_args[0] == "PRLE-2026-00001"
        assert update_args[1]["total_gross"] == base_salary
        assert update_args[1]["total_deductions"] == total_deduction
        assert update_args[1]["total_net"] == expected_net

    def test_시간외근무_수당_계산(self, mock_db) -> None:
        """10시간 overtime → 10 x (3000000/209) x 1.5 수당을 검증한다."""
        base_salary = 3_000_000
        overtime_hours = 10
        expected_overtime = round(overtime_hours * (base_salary / 209) * 1.5)

        entry_data = {
            "_id": "PRLE-2026-00002",
            "payroll_date": None,
            "start_date": None,
            "end_date": None,
            "employees": [
                {
                    "employee_id": "EMP-002",
                    "employee_name": "김철수",
                    "base_salary": base_salary,
                    "overtime_hours": overtime_hours,
                    "bonus": 0,
                    "allowances": 0,
                    "dependents": 1,
                },
            ],
        }
        mock_db["payroll_repo"].find_by_id.return_value = entry_data

        service = PayrollCalculationService(tenant_id="test-tenant")
        slip_ids = service.process_payroll("PRLE-2026-00002")

        assert len(slip_ids) == 1

        # SalarySlip insert 호출 확인
        insert_call = mock_db["slip_repo"].insert.call_args
        slip: object = insert_call[0][0]
        assert slip.gross_pay == round(base_salary + expected_overtime)

        # earnings에 시간외근무수당 항목이 있는지 확인
        overtime_earning = next((e for e in slip.earnings if e.component == "시간외근무수당"), None)
        assert overtime_earning is not None
        assert overtime_earning.amount == expected_overtime

    def test_영_급여_처리(self, mock_db) -> None:
        """base_salary 0 → 공제 0, net 0 검증."""
        entry_data = {
            "_id": "PRLE-2026-00003",
            "payroll_date": None,
            "start_date": None,
            "end_date": None,
            "employees": [
                {
                    "employee_id": "EMP-003",
                    "employee_name": "이영희",
                    "base_salary": 0,
                    "overtime_hours": 0,
                    "bonus": 0,
                    "allowances": 0,
                    "dependents": 1,
                },
            ],
        }
        mock_db["payroll_repo"].find_by_id.return_value = entry_data

        service = PayrollCalculationService(tenant_id="test-tenant")
        slip_ids = service.process_payroll("PRLE-2026-00003")

        assert len(slip_ids) == 1

        insert_call = mock_db["slip_repo"].insert.call_args
        slip: object = insert_call[0][0]
        assert slip.gross_pay == 0
        assert slip.total_deduction == 0
        assert slip.net_pay == 0

    def test_고소득_구간(self, mock_db) -> None:
        """1000만원 급여 → 높은 세율 적용 검증."""
        base_salary = 10_000_000

        entry_data = {
            "_id": "PRLE-2026-00004",
            "payroll_date": None,
            "start_date": None,
            "end_date": None,
            "employees": [
                {
                    "employee_id": "EMP-004",
                    "employee_name": "박대기",
                    "base_salary": base_salary,
                    "overtime_hours": 0,
                    "bonus": 0,
                    "allowances": 0,
                    "dependents": 1,
                },
            ],
        }
        mock_db["payroll_repo"].find_by_id.return_value = entry_data

        service = PayrollCalculationService(tenant_id="test-tenant")
        slip_ids = service.process_payroll("PRLE-2026-00004")

        assert len(slip_ids) == 1

        insert_call = mock_db["slip_repo"].insert.call_args
        slip: object = insert_call[0][0]

        # 소득세 확인
        income_tax_item = next((d for d in slip.deductions if d.component == "소득세"), None)
        assert income_tax_item is not None
        assert income_tax_item.amount == 904_600

        # 지방소득세 확인
        local_tax_item = next((d for d in slip.deductions if d.component == "지방소득세"), None)
        assert local_tax_item is not None
        assert local_tax_item.amount == round(904_600 * 0.1)

    def test_부양가족_3인_공제(self, mock_db) -> None:
        """부양가족 3인(본인+2인) → 소득세 25,000원 감면 검증."""
        base_salary = 3_000_000

        # 부양가족 1인 기준 소득세
        tax_1 = IncomeTaxService.calculate_monthly_tax(base_salary, 1)
        # 부양가족 3인 기준 소득세
        tax_3 = IncomeTaxService.calculate_monthly_tax(base_salary, 3)
        assert tax_1 - tax_3 == 25_000

        entry_data = {
            "_id": "PRLE-2026-00005",
            "payroll_date": None,
            "start_date": None,
            "end_date": None,
            "employees": [
                {
                    "employee_id": "EMP-005",
                    "employee_name": "최민수",
                    "base_salary": base_salary,
                    "overtime_hours": 0,
                    "bonus": 0,
                    "allowances": 0,
                    "dependents": 3,
                },
            ],
        }
        mock_db["payroll_repo"].find_by_id.return_value = entry_data

        service = PayrollCalculationService(tenant_id="test-tenant")
        slip_ids = service.process_payroll("PRLE-2026-00005")

        assert len(slip_ids) == 1

        insert_call = mock_db["slip_repo"].insert.call_args
        slip: object = insert_call[0][0]

        income_tax_item = next((d for d in slip.deductions if d.component == "소득세"), None)
        assert income_tax_item is not None
        assert income_tax_item.amount == tax_3  # 25,000 감면

    def test_급여대장_미존재_예외(self, mock_db) -> None:
        """존재하지 않는 PayrollEntry에 대해 OneERPError(404)가 발생하는지 검증한다."""
        mock_db["payroll_repo"].find_by_id.return_value = None

        service = PayrollCalculationService(tenant_id="test-tenant")
        with pytest.raises(OneERPError) as exc_info:
            service.process_payroll("PRLE-NONEXISTENT")
        assert exc_info.value.status_code == 404
        assert "급여대장을 찾을 수 없습니다" in str(exc_info.value.detail)

    def test_직원_없는_급여대장(self, mock_db) -> None:
        """직원 목록이 비어있으면 빈 리스트를 반환하는지 검증한다."""
        entry_data = {
            "_id": "PRLE-2026-00006",
            "employees": [],
        }
        mock_db["payroll_repo"].find_by_id.return_value = entry_data

        service = PayrollCalculationService(tenant_id="test-tenant")
        slip_ids = service.process_payroll("PRLE-2026-00006")

        assert slip_ids == []

    def test_복수_직원_처리(self, mock_db) -> None:
        """복수 직원 급여 처리 시 합계가 정확한지 검증한다."""
        entry_data = {
            "_id": "PRLE-2026-00007",
            "payroll_date": None,
            "start_date": None,
            "end_date": None,
            "employees": [
                {
                    "employee_id": "EMP-010",
                    "employee_name": "직원A",
                    "base_salary": 3_000_000,
                    "overtime_hours": 0,
                    "bonus": 0,
                    "allowances": 0,
                    "dependents": 1,
                },
                {
                    "employee_id": "EMP-011",
                    "employee_name": "직원B",
                    "base_salary": 4_000_000,
                    "overtime_hours": 5,
                    "bonus": 100_000,
                    "allowances": 50_000,
                    "dependents": 2,
                },
            ],
        }
        mock_db["payroll_repo"].find_by_id.return_value = entry_data

        service = PayrollCalculationService(tenant_id="test-tenant")
        slip_ids = service.process_payroll("PRLE-2026-00007")

        assert len(slip_ids) == 2

        # PayrollEntry 합계 업데이트 확인
        update_call = mock_db["payroll_repo"].update_by_id.call_args
        assert update_call is not None
        update_data = update_call[0][1]
        assert update_data["total_gross"] > 0
        assert update_data["total_net"] > 0
        assert update_data["total_gross"] > update_data["total_net"]
