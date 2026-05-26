"""급여명세서 PDF 리포트용 전용 엔드포인트.

FE(`web/app/(modules)/reports/payslip/[id]/route.tsx`)의
`@react-pdf/renderer` 라우트가 본 엔드포인트의 응답을 그대로 컴포넌트 props 로 사용한다.

Wave 5 단계:
    - SalarySlip → PayslipResponse 매핑이 1차 경로.
    - 미존재/비정상 데이터 시 mock 기반 fallback 을 제공해 PDF 라우트가 비어 보이지 않게 한다.
    - Wave 6 이후 실제 DB 조인(HR Employee, Company)까지 정밀화 예정.

테넌트 격리는 `CurrentUserDep` 의 `tenant_id` 로 Repository 에 바인딩하여 보장한다.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_payroll_app.schemas.payslip_schemas import (
    PayslipCompanyInfo,
    PayslipEmployeeInfo,
    PayslipLineItem,
    PayslipPeriodInfo,
    PayslipResponse,
)

router = APIRouter(prefix="/api/v1/payroll/payslips", tags=["payslip-reports"])

_COLLECTION = "salary_slips"

# Wave 5 fallback 기본값 — Wave 6 에서 HR/Company 마스터 조회로 치환된다.
_FALLBACK_COMPANY = PayslipCompanyInfo(
    name="원이알피 주식회사",
    ceo="김대표",
    address="서울특별시 강남구 테헤란로 123, 10층",
    businessNumber="123-45-67890",
    phone="02-1234-5678",
)


def _today() -> date:
    """DTZ011 회피용 — UTC 기준 오늘 날짜."""
    return datetime.now(tz=UTC).date()


def _get_repo(tenant_id: str) -> Repository:
    """현재 사용자의 테넌트에 바인딩된 SalarySlip Repository."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _to_decimal(value: Any) -> Decimal:
    """FerretDB/Pydantic 이 반환하는 숫자 값을 Decimal 로 정규화한다."""
    if value is None:
        return Decimal(0)
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except ArithmeticError, ValueError:
        return Decimal(0)


def _coerce_line_items(raw: Any) -> list[PayslipLineItem]:
    """SalarySlip 의 earnings/deductions 배열을 `PayslipLineItem` 로 변환한다.

    SalaryComponent 스키마(label/amount 혹은 name/amount 등) 편차를 흡수한다.
    """
    if not isinstance(raw, list):
        return []
    items: list[PayslipLineItem] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        label = (
            entry.get("label")
            or entry.get("name")
            or entry.get("component_name")
            or entry.get("description")
            or ""
        )
        amount = _to_decimal(entry.get("amount") or entry.get("value") or 0)
        if not label:
            continue
        items.append(PayslipLineItem(label=str(label), amount=amount))
    return items


def _extract_period(doc: dict[str, Any]) -> PayslipPeriodInfo:
    """SalarySlip 의 posting_date / start_date 로부터 연/월을 도출한다."""
    candidate = doc.get("posting_date") or doc.get("start_date") or doc.get("end_date")
    if isinstance(candidate, date):
        return PayslipPeriodInfo(year=candidate.year, month=candidate.month)
    if isinstance(candidate, str) and len(candidate) >= 7:
        try:
            year = int(candidate[:4])
            month = int(candidate[5:7])
            return PayslipPeriodInfo(year=year, month=month)
        except ValueError:
            pass
    today = _today()
    return PayslipPeriodInfo(year=today.year, month=today.month)


def _fallback_payslip(payslip_id: str) -> PayslipResponse:
    """Wave 5 임시 fallback — SalarySlip 레코드가 없을 때 PDF 가 빈 화면이 되는 것을 방지.

    Wave 6 에서 본 함수는 제거되고 404 응답으로 전환된다.
    """
    return PayslipResponse(
        employee=PayslipEmployeeInfo(
            name="샘플 직원",
            employee_id=payslip_id,
            department="미지정",
            position="미지정",
        ),
        period=PayslipPeriodInfo(year=_today().year, month=_today().month),
        earnings=[
            PayslipLineItem(label="기본급", amount=Decimal(3000000)),
            PayslipLineItem(label="직책수당", amount=Decimal(200000)),
        ],
        deductions=[
            PayslipLineItem(label="국민연금", amount=Decimal(135000)),
            PayslipLineItem(label="건강보험", amount=Decimal(106500)),
            PayslipLineItem(label="근로소득세", amount=Decimal(120000)),
        ],
        net_pay=Decimal(2838500),
        company=_FALLBACK_COMPANY,
        issued_at=_today().isoformat(),
    )


def _build_from_document(doc: dict[str, Any]) -> PayslipResponse:
    """SalarySlip 도큐먼트를 PayslipResponse 로 매핑한다.

    net_pay 는 document 우선, 없으면 (earnings 합 - deductions 합) 으로 재계산.
    """
    earnings = _coerce_line_items(doc.get("earnings"))
    deductions = _coerce_line_items(doc.get("deductions"))

    net_pay = _to_decimal(doc.get("net_pay"))
    if net_pay == 0:
        net_pay = sum((e.amount for e in earnings), Decimal(0)) - sum(
            (d.amount for d in deductions), Decimal(0)
        )

    employee = PayslipEmployeeInfo(
        name=str(doc.get("employee_name") or "직원"),
        employee_id=str(doc.get("employee_id") or doc.get("_id") or ""),
        department=str(doc.get("department") or ""),
        position=str(doc.get("designation") or doc.get("position") or ""),
    )

    return PayslipResponse(
        employee=employee,
        period=_extract_period(doc),
        earnings=earnings,
        deductions=deductions,
        net_pay=net_pay,
        company=_FALLBACK_COMPANY,
        issued_at=_today().isoformat(),
    )


@router.get(
    "/{payslip_id}",
    response_model=PayslipResponse,
    dependencies=[Depends(require_permission("salary_slip:read"))],
)
def get_payslip_report(payslip_id: str, user: CurrentUserDep) -> PayslipResponse:
    """급여명세서 PDF 생성용 정규화 데이터 반환.

    흐름:
        1. SalarySlip 조회(테넌트 격리)
        2. 존재 시 `_build_from_document` 로 매핑
        3. 미존재 시 Wave 5 fallback mock 반환 (Wave 6 에서 404 로 전환 예정)

    반환 구조는 `web/components/pdf/PayslipPdf.tsx` 의 `PayslipProps` 와 일치한다.
    """
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(payslip_id)
    if not doc:
        return _fallback_payslip(payslip_id)
    return _build_from_document(doc)
