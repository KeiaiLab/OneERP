"""급여명세서 PDF 리포트 응답 스키마.

`web/components/pdf/PayslipPdf.tsx` 의 `PayslipProps` 타입과 1:1 매칭된다.
FE 라우트 핸들러(`web/app/(modules)/reports/payslip/[id]/route.tsx`)가
본 스키마로 직렬화된 JSON 을 그대로 컴포넌트 props 로 전달할 수 있다.

필드명은 snake_case 를 유지한다(FE 의 PayslipProps 도 snake_case).
"""

from __future__ import annotations

from decimal import Decimal  # noqa: TC003 — Pydantic v2 런타임 필요

from pydantic import BaseModel, Field


class PayslipEmployeeInfo(BaseModel):
    """PDF 헤더에 노출되는 직원 정보."""

    name: str = Field(description="직원 성명")
    employee_id: str = Field(description="사번")
    department: str = Field(default="", description="부서")
    position: str = Field(default="", description="직급")


class PayslipPeriodInfo(BaseModel):
    """급여 지급 기간(년/월)."""

    year: int = Field(description="지급 연도", ge=1900, le=9999)
    month: int = Field(description="지급 월(1~12)", ge=1, le=12)


class PayslipLineItem(BaseModel):
    """지급/공제 세부 항목."""

    label: str = Field(description="항목명 예: 기본급, 국민연금")
    amount: Decimal = Field(description="금액 — KRW 원 단위")


class PayslipCompanyInfo(BaseModel):
    """PDF 헤더 회사 정보.

    FE `CompanyInfo` 타입과 필드명이 정확히 일치한다.
    businessNumber/phone 는 camelCase 를 유지한다(FE 원본 타입 준수).
    """

    name: str
    ceo: str
    address: str
    businessNumber: str | None = None
    phone: str | None = None


class PayslipResponse(BaseModel):
    """급여명세서 PDF 생성용 정규화된 응답.

    FE `PayslipProps` 와 1:1 매칭된다.
    BE 내부 모델(SalarySlip, PayrollEntry, Employee)을 조합/집계하여 생성된다.
    """

    employee: PayslipEmployeeInfo
    period: PayslipPeriodInfo
    earnings: list[PayslipLineItem]
    deductions: list[PayslipLineItem]
    net_pay: Decimal = Field(description="실지급액 (지급 합계 - 공제 합계)")
    company: PayslipCompanyInfo
    issued_at: str | None = Field(
        default=None,
        description="발행일(YYYY-MM-DD). FE 기본값은 오늘.",
    )
