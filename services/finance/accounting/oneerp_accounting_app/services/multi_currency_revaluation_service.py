"""다통화 일괄 재평가 서비스 — 외화 화폐성 항목 월말 재평가.

근거 표준 (K-IFRS 1021, IAS 21):
- IAS 21.23(a): 외화 화폐성 항목은 보고기간 말 종가환율로 환산
- IAS 21.28: 화폐성 항목의 환산차이는 발생 기간의 P&L 인식
- IAS 21.23(b): 비화폐성 항목 (재고, 유형자산 등)은 거래일 환율 유지

L2 비즈니스 룰 매핑:
- BR-ADV-ACC-014: 화폐성 항목만 재평가
- BR-ADV-ACC-015: 재평가 분개 역분개 (취소 시)
- BR-ADV-ACC-029: 기능통화 != 표시통화 처리
- BR-ADV-ACC-030: 월초 자동 역분개 (선택)

설계 메모:
- 화폐성 vs 비화폐성 분류는 계정과목명 키워드 + account_type 조합으로 추론.
- 정확한 분류를 위해서는 별도 마스터 (account_classification)가 권장되나,
  본 1차 구현에서는 휴리스틱 기반 (확장 시 마스터 참조 가능).
- 부채는 환율 상승 시 갚을 금액 증가하므로 평가손실 (자산과 부호 반대).
- 분개: 평가이익은 외환차익(income), 평가손실은 외환차손(expense)으로 분류.
"""

from __future__ import annotations

import logging
from datetime import date  # noqa: TC003
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from oneerp_core.document import DocStatus
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_accounting_app.models.journal_entry import JournalEntry, JournalEntryItem

logger = logging.getLogger(__name__)

# 화폐성 항목 키워드 (계정과목명에 포함되면 화폐성으로 추정)
_MONETARY_KEYWORDS_ASSET = (
    "채권",
    "예금",
    "현금",
    "미수금",
    "미수",
    "대여금",
)
_MONETARY_KEYWORDS_LIABILITY = (
    "채무",
    "차입금",
    "미지급금",
    "미지급",
    "사채",
)

# 비화폐성 명시 키워드 (자산임에도 비화폐성)
_NON_MONETARY_KEYWORDS = (
    "재고",
    "건물",
    "토지",
    "기계",
    "설비",
    "선급금",
    "특허",
    "영업권",
    "투자부동산",
)

# 원화 반올림 단위
_KRW_QUANT = Decimal(1)


def _to_decimal(value: Any) -> Decimal:
    """다양한 입력을 Decimal로 안전하게 변환한다."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def is_monetary_account(account_name: str, account_type: str) -> bool:
    """계정과목이 화폐성 항목인지 판정한다 (IAS 21.16 단순화).

    화폐성 항목: 정해진 금액으로 받거나 지급할 권리/의무 (현금, 채권, 채무, 차입금 등).
    비화폐성 항목: 재고, 유형자산, 영업권, 선급/선수 등.

    수익/비용/자본은 재평가 대상이 아니다 (P&L과 자본은 거래일 환율).
    """
    if account_type not in ("asset", "liability"):
        return False

    # 비화폐성 키워드가 명시되어 있으면 비화폐성
    if any(keyword in account_name for keyword in _NON_MONETARY_KEYWORDS):
        return False

    if account_type == "asset":
        return any(keyword in account_name for keyword in _MONETARY_KEYWORDS_ASSET)

    # liability
    return any(keyword in account_name for keyword in _MONETARY_KEYWORDS_LIABILITY)


def calculate_revaluation_diff(
    foreign_amount: Decimal,
    book_rate: Decimal,
    closing_rate: Decimal,
    account_type: str,
) -> dict[str, Any]:
    """외화 잔액 재평가 차이를 계산한다.

    Args:
        foreign_amount: 외화 잔액 (예: 10,000 USD)
        book_rate: 장부 환율 (전일 또는 거래 환율)
        closing_rate: 종가 환율 (보고일 환율)
        account_type: asset/liability

    Returns:
        {"foreign_amount", "book_value", "new_value", "diff", "is_gain", ...}

    Note:
        자산: 차이 = new_value - book_value
        부채: 부호 반전 (환율 상승 시 갚을 금액 증가하여 손실 발생)
    """
    foreign = _to_decimal(foreign_amount)
    book = _to_decimal(book_rate)
    closing = _to_decimal(closing_rate)

    book_value = (foreign * book).quantize(_KRW_QUANT, rounding=ROUND_HALF_UP)
    new_value = (foreign * closing).quantize(_KRW_QUANT, rounding=ROUND_HALF_UP)
    raw_diff = new_value - book_value

    diff = -raw_diff if account_type == "liability" else raw_diff

    return {
        "foreign_amount": foreign,
        "book_rate": book,
        "closing_rate": closing,
        "book_value": book_value,
        "new_value": new_value,
        "diff": diff,
        "is_gain": diff > 0,
    }


class MultiCurrencyRevaluationService:
    """다통화 일괄 재평가 서비스.

    월말/분기말 외화 화폐성 항목을 종가환율로 재평가하고,
    환산차이를 외환차손익 분개로 자동 인식한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._mcr_repo = Repository("multi_currency_revaluations", tenant_id=tenant_id)
        self._je_repo = Repository("journal_entries", tenant_id=tenant_id)
        self._fx_repo = Repository("currency_exchanges", tenant_id=tenant_id)

    def run_revaluation(
        self,
        revaluation_date: date,
        base_currency: str,
        closing_rates: dict[str, Decimal],
        account_balances: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """외화 잔액을 일괄 재평가한다.

        Args:
            revaluation_date: 재평가 기준일 (보통 월말)
            base_currency: 보고통화 (한국=KRW)
            closing_rates: {"USD": Decimal("1350"), "EUR": Decimal("1450"), ...}
            account_balances: [{"account", "account_type", "currency",
                                "foreign_amount", "book_rate"}, ...]

        Returns:
            재평가 요약 (총 손익, 평가이익, 평가손실, 처리/제외 건수, 상세)
        """
        details: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        skipped_currencies: set[str] = set()

        total_gain = Decimal(0)
        total_loss = Decimal(0)

        for balance in account_balances:
            account = str(balance.get("account", ""))
            account_type = str(balance.get("account_type", ""))
            currency = str(balance.get("currency", ""))

            # BR-ADV-ACC-014: 화폐성 여부 확인
            if not is_monetary_account(account, account_type):
                skipped.append(
                    {
                        "account": account,
                        "reason": "비화폐성 항목 (IAS 21.23)",
                    }
                )
                continue

            # 보고통화와 같으면 재평가 불필요
            if currency == base_currency:
                skipped.append(
                    {
                        "account": account,
                        "reason": "보고통화와 동일 통화",
                    }
                )
                continue

            # 종가환율 누락 확인
            closing_rate = closing_rates.get(currency)
            if closing_rate is None:
                skipped.append(
                    {
                        "account": account,
                        "reason": f"{currency} 종가환율 누락",
                    }
                )
                skipped_currencies.add(currency)
                continue

            calc = calculate_revaluation_diff(
                foreign_amount=_to_decimal(balance.get("foreign_amount", 0)),
                book_rate=_to_decimal(balance.get("book_rate", 0)),
                closing_rate=_to_decimal(closing_rate),
                account_type=account_type,
            )

            details.append(
                {
                    "account": account,
                    "account_type": account_type,
                    "currency": currency,
                    **{k: v for k, v in calc.items() if k != "is_gain"},
                    "is_gain": calc["is_gain"],
                }
            )

            if calc["is_gain"]:
                total_gain += calc["diff"]
            else:
                total_loss += abs(calc["diff"])

        total_gain_loss = total_gain - total_loss

        result = {
            "revaluation_date": revaluation_date.isoformat(),
            "base_currency": base_currency,
            "accounts_revalued": len(details),
            "accounts_skipped": len(skipped),
            "skipped": skipped,
            "skipped_currencies": sorted(skipped_currencies),
            "total_gain": total_gain,
            "total_loss": total_loss,
            "total_gain_loss": total_gain_loss,
            "details": details,
        }

        logger.info(
            "다통화 재평가 완료: %s, 처리=%d건, 제외=%d건, 순손익=%s",
            revaluation_date.isoformat(),
            len(details),
            len(skipped),
            total_gain_loss,
        )

        return result

    def generate_revaluation_journal(
        self,
        account: str,
        account_type: str,
        diff: Decimal,
        revaluation_date: date,
        currency: str,
    ) -> str | None:
        """재평가 차이에 대한 분개를 생성한다.

        평가이익: 차변=대상 계정, 대변=외환차익(income)
        평가손실: 차변=외환차손(expense), 대변=대상 계정

        Returns:
            생성된 분개 ID, 차이가 0이면 None
        """
        diff_amount = _to_decimal(diff)
        if diff_amount == 0:
            logger.info("재평가 차이 0원 — 분개 생성 생략 (%s)", account)
            return None

        abs_diff = abs(diff_amount)

        if diff_amount > 0:
            # 평가이익
            items = [
                JournalEntryItem(
                    account=account,
                    account_type=account_type,
                    debit=abs_diff,
                    credit=Decimal(0),
                ),
                JournalEntryItem(
                    account="외환차익",
                    account_type="income",
                    debit=Decimal(0),
                    credit=abs_diff,
                ),
            ]
        else:
            # 평가손실
            items = [
                JournalEntryItem(
                    account="외환차손",
                    account_type="expense",
                    debit=abs_diff,
                    credit=Decimal(0),
                ),
                JournalEntryItem(
                    account=account,
                    account_type=account_type,
                    debit=Decimal(0),
                    credit=abs_diff,
                ),
            ]

        je_id = generate_name("JE", tenant_id=self._tenant_id)
        je = JournalEntry(
            _id=je_id,
            posting_date=revaluation_date,
            voucher_type="fx_revaluation",
            voucher_no=f"REVAL-{currency}-{revaluation_date.isoformat()}",
            total_debit=abs_diff,
            total_credit=abs_diff,
            items=items,
            remark=f"{currency} 외화 재평가 ({account}, {diff_amount:+,}원)",
            docstatus=DocStatus.SUBMITTED,
            tenant_id=self._tenant_id,
        )
        self._je_repo.insert(je)

        logger.info(
            "재평가 분개 생성: %s (%s, 차이=%s)",
            je_id,
            account,
            diff_amount,
        )

        return je_id
