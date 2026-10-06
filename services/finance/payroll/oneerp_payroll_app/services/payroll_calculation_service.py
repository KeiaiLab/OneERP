"""급여 계산 엔진 — PayrollEntry 기반 급여 일괄 처리.

PayrollEntry의 직원 목록을 순회하며 각 직원별 SalarySlip을 생성한다.
기본급 + 시간외수당 + 상여금 + 수당 - 4대보험 - 소득세 - 지방소득세를 계산한다.

L2 비즈니스 룰 매핑:
- BR-PAY-001: gross = base + overtime + bonus + allowances
- BR-PAY-002~005: 4대보험(SocialInsuranceService + KoreanInsuranceService)
- BR-PAY-006: 소득세 간이세액표 (IncomeTaxService)
- BR-PAY-007: 지방소득세 = 소득세 x 10%
- BR-PAY-008: net = gross - (4대보험 + 소득세 + 지방소득세)
- BR-PAY-018: 사업주 부담(employer_burden) 별도 기록
"""

from __future__ import annotations

import logging
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, cast

from oneerp_core.errors import raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_payroll_app.models.salary_slip import SalarySlip
from oneerp_payroll_app.models.salary_structure import SalaryComponent
from oneerp_payroll_app.services.income_tax_service import IncomeTaxService
from oneerp_payroll_app.services.korean_insurance_service import KoreanInsuranceService
from oneerp_payroll_app.services.social_insurance_service import SocialInsuranceService

logger = logging.getLogger(__name__)

# 시간외근무 수당 계산 기준: 월 소정근로시간 209시간, 1.5배
_MONTHLY_STANDARD_HOURS = Decimal(209)
_OVERTIME_MULTIPLIER = Decimal("1.5")


def _round_won(value: Decimal) -> Decimal:
    """원 단위로 반올림한다 (소수점 이하 제거, ROUND_HALF_UP)."""
    return value.quantize(Decimal(1), rounding=ROUND_HALF_UP)


class PayrollCalculationService:
    """급여 계산 서비스.

    PayrollEntry를 기반으로 직원별 SalarySlip을 생성하고,
    PayrollEntry의 합계를 업데이트한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = tenant_id
        self._payroll_repo = Repository("payroll_entries", tenant_id=tenant_id)
        self._slip_repo = Repository("salary_slips", tenant_id=tenant_id)
        self._additional_salary_repo = Repository("additional_salaries", tenant_id=tenant_id)
        self._loan_repo = Repository("employee_loans", tenant_id=tenant_id)
        self._insurance_service = SocialInsuranceService(tenant_id=tenant_id)
        # KoreanInsuranceService 는 확장 API(상한/하한/업종요율/employer_burden) 전용
        self._korean_insurance = KoreanInsuranceService()

    def _get_additional_salary(self, employee_id: str, _payroll_entry_id: str) -> Decimal:
        """BR-PAY-016: 해당 급여대장 기간의 추가급여를 합산한다."""
        docs = self._additional_salary_repo.find_many(
            {"employee_id": employee_id, "is_active": True},
            limit=100,
        )
        return sum((Decimal(str(d.get("amount", 0))) for d in docs), Decimal(0))

    def _get_loan_deduction(self, employee_id: str) -> Decimal:
        """BR-PAY-017: 활성 대출의 월 상환액을 합산한다."""
        loans = self._loan_repo.find_many(
            {"employee_id": employee_id, "status": "active"},
            limit=100,
        )
        return sum((Decimal(str(ln.get("monthly_repayment", 0))) for ln in loans), Decimal(0))

    def process_payroll(self, payroll_entry_id: str) -> list[str]:
        """급여대장(PayrollEntry)을 처리하여 SalarySlip 목록을 생성한다.

        Args:
            payroll_entry_id: PayrollEntry 문서 ID

        Returns:
            생성된 SalarySlip ID 목록

        Raises:
            OneERPError: PayrollEntry를 찾을 수 없을 때 (404)
        """
        entry = self._payroll_repo.find_by_id(payroll_entry_id)
        if not entry:
            raise_not_found(f"ERR-PAY-002: 급여대장을 찾을 수 없습니다: {payroll_entry_id}")
        entry = cast("dict[str, Any]", entry)

        employees: list[dict[str, Any]] = entry.get("employees", [])
        if not employees:
            logger.warning("급여대장에 직원이 없습니다: %s", payroll_entry_id)
            return []

        slip_ids: list[str] = []
        total_gross = Decimal(0)
        total_deductions = Decimal(0)
        total_net = Decimal(0)
        total_employer_burden = Decimal(0)

        for emp_entry in employees:
            result = self._calculate_single(emp_entry, entry, payroll_entry_id)
            slip_id = result["slip_id"]
            slip_ids.append(slip_id)
            total_gross += result["gross_pay"]
            total_deductions += result["total_deduction"]
            total_net += result["net_pay"]
            total_employer_burden += result["employer_burden"]

        # PayrollEntry 합계 업데이트 (BR-PAY-018: 사업주 부담 별도 기록)
        self._payroll_repo.update_by_id(
            payroll_entry_id,
            {
                "total_gross": _round_won(total_gross),
                "total_deductions": _round_won(total_deductions),
                "total_net": _round_won(total_net),
                "total_employer_burden": _round_won(total_employer_burden),
            },
        )

        logger.info(
            "급여 처리 완료: entry=%s, slips=%d, gross=%s, net=%s",
            payroll_entry_id,
            len(slip_ids),
            total_gross,
            total_net,
        )

        return slip_ids

    def _calculate_single(
        self,
        emp_entry: dict[str, Any],
        entry: dict[str, Any],
        payroll_entry_id: str = "",
    ) -> dict[str, Any]:
        """개별 직원의 급여를 계산하고 SalarySlip을 생성한다.

        Args:
            emp_entry: 직원별 급여 입력 데이터
            entry: PayrollEntry 원본 데이터
            payroll_entry_id: 급여대장 참조 ID

        Returns:
            계산 결과 딕셔너리 (slip_id, gross_pay, total_deduction, net_pay)
        """
        employee_id: str = emp_entry.get("employee_id", "")
        employee_name: str = emp_entry.get("employee_name", "")
        base_salary = Decimal(str(emp_entry.get("base_salary", 0)))
        overtime_hours = Decimal(str(emp_entry.get("overtime_hours", 0)))
        bonus = Decimal(str(emp_entry.get("bonus", 0)))
        allowances = Decimal(str(emp_entry.get("allowances", 0)))
        dependents: int = int(emp_entry.get("dependents", 1))

        # --- 지급 항목 계산 (BR-PAY-001) ---
        earnings: list[SalaryComponent] = []

        # 기본급
        earnings.append(SalaryComponent(component="기본급", amount=_round_won(base_salary)))

        # 시간외근무 수당
        overtime_pay = Decimal(0)
        if overtime_hours > 0 and base_salary > 0:
            hourly_rate = base_salary / _MONTHLY_STANDARD_HOURS
            overtime_pay = _round_won(overtime_hours * hourly_rate * _OVERTIME_MULTIPLIER)
            earnings.append(SalaryComponent(component="시간외근무수당", amount=overtime_pay))

        # 상여금
        if bonus > 0:
            earnings.append(SalaryComponent(component="상여금", amount=_round_won(bonus)))

        # 수당
        if allowances > 0:
            earnings.append(SalaryComponent(component="수당", amount=_round_won(allowances)))

        # BR-PAY-016: 추가급여 반영 (해당 월 활성 추가급여 합산)
        additional_salary_total = self._get_additional_salary(employee_id, payroll_entry_id)
        if additional_salary_total > 0:
            earnings.append(
                SalaryComponent(component="추가급여", amount=_round_won(additional_salary_total))
            )

        gross_pay = _round_won(
            base_salary + overtime_pay + bonus + allowances + additional_salary_total
        )

        # --- 공제 항목 계산 ---
        deductions: list[SalaryComponent] = []

        # 4대보험
        insurance = self._insurance_service.calculate(base_salary)
        deductions.append(
            SalaryComponent(component="국민연금", amount=insurance.national_pension_employee)
        )
        deductions.append(
            SalaryComponent(component="건강보험", amount=insurance.health_insurance_employee)
        )
        deductions.append(
            SalaryComponent(component="장기요양보험", amount=insurance.long_term_care_employee)
        )
        deductions.append(
            SalaryComponent(component="고용보험", amount=insurance.employment_insurance_employee)
        )

        # 소득세 — BR-PAY-006: 간이세액표 (float 기반 → Decimal 변환)
        income_tax = Decimal(
            str(IncomeTaxService.calculate_monthly_tax(float(gross_pay), dependents))
        )
        deductions.append(SalaryComponent(component="소득세", amount=income_tax))

        # 지방소득세 — BR-PAY-007
        local_income_tax = Decimal(
            str(IncomeTaxService.calculate_local_income_tax(float(income_tax)))
        )
        deductions.append(SalaryComponent(component="지방소득세", amount=local_income_tax))

        # BR-PAY-017: 직원대출 월 상환 공제
        loan_deduction = self._get_loan_deduction(employee_id)
        if loan_deduction > 0:
            deductions.append(SalaryComponent(component="대출상환", amount=loan_deduction))

        # BR-PAY-008: 실수령액 = gross_pay - (4대보험 + 소득세 + 지방소득세 + 대출상환)
        total_deduction = _round_won(
            insurance.total_employee + income_tax + local_income_tax + loan_deduction
        )
        net_pay = _round_won(gross_pay - total_deduction)

        # BR-PAY-018: 사업주 부담 합계(employer_burden)
        employer_burden = _round_won(insurance.total_employer)

        # SalarySlip 생성
        slip_id = generate_name("SLIP", tenant_id=self.tenant_id)
        slip = SalarySlip(
            _id=slip_id,
            tenant_id=self.tenant_id,
            employee_id=employee_id,
            employee_name=employee_name,
            payroll_entry_id=payroll_entry_id,
            posting_date=entry.get("payroll_date"),
            start_date=entry.get("start_date"),
            end_date=entry.get("end_date"),
            gross_pay=gross_pay,
            total_deduction=total_deduction,
            net_pay=net_pay,
            earnings=earnings,
            deductions=deductions,
        )
        self._slip_repo.insert(slip)

        logger.info(
            "급여명세 생성: slip=%s, gross=%s, net=%s",
            slip_id,
            gross_pay,
            net_pay,
        )

        return {
            "slip_id": slip_id,
            "gross_pay": gross_pay,
            "total_deduction": total_deduction,
            "net_pay": net_pay,
            "employer_burden": employer_burden,
        }

    # --- 단순 API: 단일 직원 급여 계산 (KoreanInsuranceService 래퍼) ---------

    def calculate_payroll(
        self,
        *,
        gross_pay: Decimal,
        dependents: int = 1,
        industry_rate: Decimal = Decimal("0.01"),
    ) -> dict[str, Decimal]:
        """단일 직원의 급여(공제 + 실수령 + 사업주 부담)를 계산한다.

        PayrollEntry 배치와 무관한 단순 계산기 용도의 API이다.
        4대보험, 원천징수, 지방소득세, 실수령액, 사업주 부담을 모두 포함한
        딕셔너리를 반환한다.

        Args:
            gross_pay: 총 지급액
            dependents: 부양가족 수 (본인 포함, 최소 1)
            industry_rate: 산재보험 업종 요율 (디폴트 1.0%)

        Returns:
            {
                "gross_pay": ...,
                "national_pension": ...,
                "health_insurance": ...,
                "long_term_care": ...,
                "employment_insurance": ...,
                "income_tax": ...,
                "local_income_tax": ...,
                "total_deduction": ...,
                "net_pay": ...,
                "employer_burden": ...,
            }
        """
        breakdown = self._korean_insurance.calculate_payroll(
            gross_pay=gross_pay,
            dependents=dependents,
            industry_rate=industry_rate,
        )
        return {
            "gross_pay": breakdown.gross_pay,
            "national_pension": breakdown.national_pension,
            "health_insurance": breakdown.health_insurance,
            "long_term_care": breakdown.long_term_care,
            "employment_insurance": breakdown.employment_insurance,
            "income_tax": breakdown.income_tax,
            "local_income_tax": breakdown.local_income_tax,
            "total_deduction": breakdown.total_deduction,
            "net_pay": breakdown.net_pay,
            "employer_burden": breakdown.employer_burden,
        }
