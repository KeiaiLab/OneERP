"""사회보험(SocialInsurance) 문서 모델 — Payroll 모듈.

4대보험 자동 산출 결과를 포함하는 확장 모델.
사용자/사업주 분리 및 장기요양보험을 지원한다.
"""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class SocialInsuranceCreate(BaseModel):
    """사회보험 생성 요청 스키마."""

    employee_id: str
    period: str = ""
    base_salary: Decimal = Decimal(0)
    national_pension: Decimal = Decimal(0)
    national_pension_employee: Decimal = Decimal(0)
    national_pension_employer: Decimal = Decimal(0)
    health_insurance: Decimal = Decimal(0)
    health_insurance_employee: Decimal = Decimal(0)
    health_insurance_employer: Decimal = Decimal(0)
    long_term_care_employee: Decimal = Decimal(0)
    long_term_care_employer: Decimal = Decimal(0)
    employment_insurance: Decimal = Decimal(0)
    employment_insurance_employee: Decimal = Decimal(0)
    employment_insurance_employer: Decimal = Decimal(0)
    industrial_accident: Decimal = Decimal(0)
    industrial_accident_employer: Decimal = Decimal(0)
    total_employee: Decimal = Decimal(0)
    total_employer: Decimal = Decimal(0)
    total: Decimal = Decimal(0)


class SocialInsuranceUpdate(BaseModel):
    """사회보험 수정 요청 스키마."""

    period: str | None = None
    base_salary: Decimal | None = None
    national_pension: Decimal | None = None
    national_pension_employee: Decimal | None = None
    national_pension_employer: Decimal | None = None
    health_insurance: Decimal | None = None
    health_insurance_employee: Decimal | None = None
    health_insurance_employer: Decimal | None = None
    long_term_care_employee: Decimal | None = None
    long_term_care_employer: Decimal | None = None
    employment_insurance: Decimal | None = None
    employment_insurance_employee: Decimal | None = None
    employment_insurance_employer: Decimal | None = None
    industrial_accident: Decimal | None = None
    industrial_accident_employer: Decimal | None = None
    total_employee: Decimal | None = None
    total_employer: Decimal | None = None
    total: Decimal | None = None


class SocialInsurance(BaseDocument):
    """사회보험 문서 — Payroll 4대 보험 관리.

    naming prefix: SI

    4대보험(국민연금, 건강보험, 고용보험, 산재보험)의
    사용자/사업주 부담분을 분리하여 관리한다.
    장기요양보험은 건강보험에서 파생된다.
    """

    employee_id: str = ""
    period: str = ""
    base_salary: Decimal = Decimal(0)

    # 국민연금
    national_pension: Decimal = Decimal(0)
    national_pension_employee: Decimal = Decimal(0)
    national_pension_employer: Decimal = Decimal(0)

    # 건강보험
    health_insurance: Decimal = Decimal(0)
    health_insurance_employee: Decimal = Decimal(0)
    health_insurance_employer: Decimal = Decimal(0)

    # 장기요양보험
    long_term_care_employee: Decimal = Decimal(0)
    long_term_care_employer: Decimal = Decimal(0)

    # 고용보험
    employment_insurance: Decimal = Decimal(0)
    employment_insurance_employee: Decimal = Decimal(0)
    employment_insurance_employer: Decimal = Decimal(0)

    # 산재보험
    industrial_accident: Decimal = Decimal(0)
    industrial_accident_employer: Decimal = Decimal(0)

    # 합계
    total_employee: Decimal = Decimal(0)
    total_employer: Decimal = Decimal(0)
    total: Decimal = Decimal(0)
