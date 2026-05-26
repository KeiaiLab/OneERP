"""경비 정책 검증 서비스 — 한국 경비처리 표준 기반.

BR-EXP-NEW-016: 경비 항목이 회사 정책 및 세법을 준수하는지 검증.

검증 항목:
1. 유형별 1건당 한도 초과 여부
2. 영수증/증빙 필수 여부 (30,000원 이상 시 필수)
3. 부가세 매입세액공제 가능성 (국세청 기준)
   - 일반 식당/교통/사무용품: 공제 가능
   - 면세 가맹점(병원/학원), 접대비(기업업무추진비): 공제 불가

참조: 국세청 사업용 신용카드 등록 제도, 부가가치세법 제39조(매입세액 불공제).
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.errors import raise_bad_request
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# 경비 유형별 1건당 기본 한도 (원)
# 한국 일반 기업 정책 및 공무원 여비규정 참조.
_DEFAULT_LIMITS: dict[str, int] = {
    "식비": 50_000,
    "교통비": 100_000,
    "숙박비": 150_000,
    "접대비": 500_000,
    "의료비": 0,  # 원칙적으로 복리후생비 외 불공제
    "도서구입비": 200_000,
    "소모품비": 300_000,
    "통신비": 100_000,
    "법인카드": 1_000_000,
}

# 영수증 필수 금액 기준 (원)
# 소득세법 시행령 제208조의2에 따라 3만원 초과 시 적격증빙 필수.
_RECEIPT_REQUIRED_THRESHOLD = 30_000

# 부가세 매입세액 불공제 경비 유형 (부가가치세법 제39조)
_VAT_NOT_DEDUCTIBLE_TYPES: set[str] = {
    "접대비",  # 기업업무추진비
    "의료비",  # 면세 의료용역
    "교육비",  # 면세 교육용역
}

# 면세 가맹점 키워드 (매입세액 공제 불가)
_VAT_NOT_DEDUCTIBLE_MERCHANTS: tuple[str, ...] = (
    "병원",
    "의원",
    "약국",
    "학원",
    "입시",
    "룸살롱",
    "단란주점",
)


class ExpensePolicyValidator:
    """경비 정책 검증 비즈니스 로직.

    경비 청구 제출 전 한도/영수증/부가세 공제 가능성을 검증한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        # 테넌트별 커스텀 한도를 보관하기 위한 repo (미사용 시 기본값 사용)
        self._type_repo = Repository("expense_types", tenant_id=tenant_id)

    def validate_claim(
        self,
        *,
        expense_type: str,
        amount: float,
        has_receipt: bool,
        merchant: str = "",
    ) -> dict[str, Any]:
        """단일 경비 항목을 정책 기준으로 검증한다.

        Args:
            expense_type: 경비 유형 (예: "식비", "교통비")
            amount: 금액 (원)
            has_receipt: 영수증/증빙 보유 여부
            merchant: 가맹점명 (부가세 공제 판정에 사용)

        Returns:
            {valid, violations, vat_deductible, expense_type, amount}
        """
        violations: list[dict[str, str]] = []

        # 1. 한도 검증
        limit = _DEFAULT_LIMITS.get(expense_type)
        if limit is not None and limit > 0 and amount > limit:
            violations.append(
                {
                    "code": "LIMIT_EXCEEDED",
                    "message": (
                        f"{expense_type} 1건당 한도({limit:,}원)를 초과했습니다 "
                        f"(요청: {amount:,.0f}원)"
                    ),
                }
            )

        # 2. 영수증 필수 검증
        if amount >= _RECEIPT_REQUIRED_THRESHOLD and not has_receipt:
            violations.append(
                {
                    "code": "RECEIPT_REQUIRED",
                    "message": (
                        f"{_RECEIPT_REQUIRED_THRESHOLD:,}원 이상 경비는 "
                        "적격증빙(세금계산서/현금영수증/신용카드영수증)이 필수입니다"
                    ),
                }
            )

        # 3. 부가세 매입세액공제 가능성 판정
        vat_deductible = self._is_vat_deductible(expense_type, merchant)
        if not vat_deductible:
            violations.append(
                {
                    "code": "VAT_NOT_DEDUCTIBLE",
                    "message": (
                        f"부가세 매입세액공제 대상이 아닙니다 "
                        f"(유형: {expense_type}, 가맹점: {merchant})"
                    ),
                }
            )

        valid = len(violations) == 0
        logger.info(
            "경비 정책 검증: 유형=%s, 금액=%.2f, 위반=%d건, 공제가능=%s",
            expense_type,
            amount,
            len(violations),
            vat_deductible,
        )

        return {
            "valid": valid,
            "expense_type": expense_type,
            "amount": amount,
            "merchant": merchant,
            "violations": violations,
            "vat_deductible": vat_deductible,
        }

    def validate_claim_items(
        self,
        *,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """여러 경비 항목을 일괄 검증한다.

        Args:
            items: [{"expense_type", "amount", "has_receipt", "merchant"}, ...]

        Returns:
            {total_items, valid_count, results}

        Raises:
            OneERPError: items가 비어 있을 때 (400)
        """
        if not items:
            raise_bad_request("검증할 경비 항목이 비어 있습니다")

        results = [
            self.validate_claim(
                expense_type=str(item.get("expense_type", "")),
                amount=float(item.get("amount", 0)),
                has_receipt=bool(item.get("has_receipt", False)),
                merchant=str(item.get("merchant", "")),
            )
            for item in items
        ]

        valid_count = sum(1 for r in results if r["valid"])

        logger.info(
            "경비 일괄 검증: 총 %d건 / 통과 %d건 / 위반 %d건",
            len(items),
            valid_count,
            len(items) - valid_count,
        )

        return {
            "total_items": len(items),
            "valid_count": valid_count,
            "invalid_count": len(items) - valid_count,
            "results": results,
        }

    @staticmethod
    def _is_vat_deductible(expense_type: str, merchant: str) -> bool:
        """부가세 매입세액공제 가능 여부를 판정한다.

        - 경비 유형이 _VAT_NOT_DEDUCTIBLE_TYPES에 속하면 불공제
        - 가맹점명에 _VAT_NOT_DEDUCTIBLE_MERCHANTS 키워드가 포함되면 불공제
        """
        if expense_type in _VAT_NOT_DEDUCTIBLE_TYPES:
            return False

        merchant_lower = merchant.lower()
        for keyword in _VAT_NOT_DEDUCTIBLE_MERCHANTS:
            if keyword in merchant_lower or keyword in merchant:
                return False

        return True
