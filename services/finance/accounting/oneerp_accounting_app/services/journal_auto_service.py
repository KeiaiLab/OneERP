"""자동 분개 서비스 — 거래 전표 기반 복식부기 분개 자동 생성.

매출전표, 매입전표, 수금/지급, 경비, 급여 등 다양한 거래에서
복식부기 원칙(차변 합계 = 대변 합계)에 따라 분개전표를 자동 생성한다.

L2 비즈니스 룰 매핑:
- BR-ACCT-001: 차대변 합계 일치 (Decimal, 허용오차 1e-9)
- BR-ACCT-003: 마감된 회계기간 전기 금지
- BR-ACCT-005: 매출 확정 시 자동 분개 생성
- BR-ACCT-006: 매입 확정 시 자동 분개 생성
- BR-ACCT-007: 수금 확정 시 자동 분개 생성
- BR-ACCT-008: 지급 확정 시 자동 분개 생성
- BR-ACCT-009: 경비 승인 시 자동 분개 생성
- BR-ACCT-010: 급여 제출 시 자동 분개 생성 (6계정)
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.events.outbox import OutboxMixin
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_accounting_app.models.accounts_payable import AccountsPayable
from oneerp_accounting_app.models.accounts_receivable import AccountsReceivable
from oneerp_accounting_app.models.journal_entry import JournalEntry, JournalEntryItem

logger = logging.getLogger(__name__)

# 금액 비교 허용 오차
_TOLERANCE = Decimal("0.000000001")
# 원화 반올림 단위 (소수점 0자리)
_KRW_QUANT = Decimal(1)


def _to_decimal(value: Any) -> Decimal:
    """다양한 입력을 Decimal로 안전하게 변환한다."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value)).quantize(_KRW_QUANT, rounding=ROUND_HALF_UP)


def _build_sales_accounts(
    grand_total: Decimal,
    net_total: Decimal,
    tax_amount: Decimal,
    customer: str,
) -> list[dict[str, Any]]:
    """BR-ACCT-005: 매출 분개 계정을 구성한다. 음수(반품) 시 차대변 역전."""
    if grand_total < 0:
        abs_grand = abs(grand_total)
        abs_net = abs(net_total)
        abs_tax = abs_grand - abs_net
        accounts: list[dict[str, Any]] = [
            {
                "account": "매출채권",
                "account_type": "asset",
                "debit": Decimal(0),
                "credit": abs_grand,
                "party": customer,
            },
            {"account": "매출", "account_type": "income", "debit": abs_net, "credit": Decimal(0)},
        ]
        if abs_tax > 0:
            accounts.append(
                {
                    "account": "부가세예수금",
                    "account_type": "liability",
                    "debit": abs_tax,
                    "credit": Decimal(0),
                }
            )
        return accounts

    accounts = [
        {
            "account": "매출채권",
            "account_type": "asset",
            "debit": grand_total,
            "credit": Decimal(0),
            "party": customer,
        },
        {"account": "매출", "account_type": "income", "debit": Decimal(0), "credit": net_total},
    ]
    if tax_amount > 0:
        accounts.append(
            {
                "account": "부가세예수금",
                "account_type": "liability",
                "debit": Decimal(0),
                "credit": tax_amount,
            }
        )
    return accounts


class JournalAutoService:
    """거래 전표 기반 자동 분개 서비스.

    모든 금액을 Decimal로 처리하고 차변 합계 = 대변 합계를 강제한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._je_repo = Repository("journal_entries", tenant_id=tenant_id)
        self._ar_repo = Repository("accounts_receivable", tenant_id=tenant_id)
        self._ap_repo = Repository("accounts_payable", tenant_id=tenant_id)
        self._period_repo = Repository("accounting_periods", tenant_id=tenant_id)

    def _check_period_open(self, posting_date: date) -> None:
        """BR-ACCT-003: 마감된 회계기간에 전기할 수 없다.

        posting_date가 속하는 회계기간이 closed 상태이면 에러를 발생시킨다.
        회계기간이 존재하지 않는 경우는 허용한다 (기간 미등록 상태).
        """
        periods = self._period_repo.find_many(
            {
                "start_date": {"$lte": posting_date},
                "end_date": {"$gte": posting_date},
            },
            limit=1,
        )
        if periods and periods[0].get("status") == "closed":
            raise_unprocessable(
                "ERR-ACCT-031",
                f"마감된 회계기간에는 전표를 입력할 수 없습니다 (전기일: {posting_date})",
            )

    def _create_journal_entry(
        self,
        voucher_type: str,
        voucher_no: str,
        posting_date: date,
        accounts: list[dict[str, Any]],
        remark: str,
    ) -> str:
        """복식부기 분개전표를 생성한다.

        BR-ACCT-001: 차대변 합계가 일치해야 한다 (Decimal 정밀도).
        BR-ACCT-003: 마감된 기간에는 전기할 수 없다.

        Returns:
            생성된 분개전표 ID

        Raises:
            OneERPError(ERR-ACCT-030): 차대변 불일치
            OneERPError(ERR-ACCT-031): 마감 기간 전기
        """
        # BR-ACCT-003: 마감 기간 검증
        self._check_period_open(posting_date)

        total_debit = sum((_to_decimal(a.get("debit", 0)) for a in accounts), Decimal(0))
        total_credit = sum((_to_decimal(a.get("credit", 0)) for a in accounts), Decimal(0))

        # BR-ACCT-001: 차대변 일치 검증
        if abs(total_debit - total_credit) > _TOLERANCE:
            raise_unprocessable(
                "ERR-ACCT-030",
                f"차변 합계와 대변 합계가 일치하지 않습니다: "
                f"차변({total_debit}) != 대변({total_credit}) "
                f"[{voucher_type}: {voucher_no}]",
            )

        # 라인 아이템 생성
        items = []
        for idx, acc in enumerate(accounts, start=1):
            items.append(
                JournalEntryItem(
                    idx=idx,
                    account=acc["account"],
                    account_type=acc.get("account_type", ""),
                    debit=_to_decimal(acc.get("debit", 0)),
                    credit=_to_decimal(acc.get("credit", 0)),
                    cost_center=acc.get("cost_center"),
                )
            )

        je_id = generate_name("JE", tenant_id=self._tenant_id)

        # Outbox 이벤트 생성 — 분개 생성과 이벤트 기록을 원자적으로 수행
        outbox_entry = OutboxMixin.create_outbox_entry(
            event_type=EventType.JOURNAL_ENTRY_SUBMITTED,
            doc_id=je_id,
            tenant_id=self._tenant_id,
            data={
                "voucher_type": voucher_type,
                "voucher_no": voucher_no,
                "total_debit": str(total_debit),
                "total_credit": str(total_credit),
            },
        )

        je = JournalEntry(
            _id=je_id,
            tenant_id=self._tenant_id,
            posting_date=posting_date,
            voucher_type=voucher_type,
            voucher_no=voucher_no,
            total_debit=total_debit,
            total_credit=total_credit,
            items=items,
            remark=remark,
            docstatus=DocStatus.SUBMITTED,
        )
        self._je_repo.insert(je)
        # Outbox 이벤트를 별도 업데이트로 추가 — 이벤트 발행 기록
        self._je_repo.update_by_id(je_id, {"$push": {"_outbox": outbox_entry}})

        logger.info(
            "자동 분개 생성: %s (%s: %s, 금액: %s)",
            je_id,
            voucher_type,
            voucher_no,
            total_debit,
        )
        return je_id

    def create_sales_invoice_journal(self, sales_invoice_id: str) -> str:
        """BR-ACCT-005: 매출전표 분개를 생성한다.

        차변: 매출채권(AR) = grand_total
        대변: 매출 = net_total
        대변: 부가세예수금 = grand_total - net_total (세액 있을 때만)
        """
        si_repo = Repository("sales_invoices", tenant_id=self._tenant_id)
        si_doc = si_repo.find_by_id(sales_invoice_id)
        if not si_doc:
            raise_not_found(f"매출전표를 찾을 수 없습니다: {sales_invoice_id}")

        grand_total = _to_decimal(si_doc.get("grand_total", 0))
        # BR-ACCT-005: grand_total=0이면 분개를 생성하지 않는다
        if grand_total == 0:
            logger.info("grand_total=0이므로 분개를 생성하지 않습니다: %s", sales_invoice_id)
            return ""
        net_total = _to_decimal(si_doc.get("net_total", 0))
        tax_amount = grand_total - net_total
        customer = si_doc.get("customer", "")
        posting_date_raw = si_doc.get("posting_date", datetime.now(tz=UTC).date())
        posting_date = (
            posting_date_raw.date() if hasattr(posting_date_raw, "date") else posting_date_raw
        )

        # BR-ACCT-005: 음수 금액(반품) 시 차대변 역전
        accounts = _build_sales_accounts(grand_total, net_total, tax_amount, customer)

        je_id = self._create_journal_entry(
            voucher_type="sales_invoice",
            voucher_no=sales_invoice_id,
            posting_date=posting_date,
            accounts=accounts,
            remark=f"매출전표 자동 분개: {sales_invoice_id}",
        )

        # AR 레코드 생성
        ar_id = generate_name("AREC", tenant_id=self._tenant_id)
        ar_doc = AccountsReceivable(
            _id=ar_id,
            tenant_id=self._tenant_id,
            customer=customer,
            outstanding_amount=grand_total,
            due_date=si_doc.get("due_date"),
            invoice_id=sales_invoice_id,
        )
        self._ar_repo.insert(ar_doc)

        return je_id

    def create_sales_invoice_journal_from_event(self, event_data: dict[str, Any]) -> str:
        """BR-ACCT-005: 이벤트 데이터에서 직접 매출 분개를 생성한다.

        차변: 매출채권(AR) = grand_total
        대변: 매출 = net_total
        대변: 부가세예수금 = grand_total - net_total (세액 있을 때만)
        """
        doc_id = event_data.get("doc_id", "")
        grand_total = _to_decimal(event_data.get("grand_total", 0))
        # BR-ACCT-005: grand_total=0이면 분개를 생성하지 않는다
        if grand_total == 0:
            logger.info("grand_total=0이므로 분개를 생성하지 않습니다: %s", doc_id)
            return ""
        net_total = _to_decimal(event_data.get("net_total", 0))
        tax_amount = grand_total - net_total
        customer = event_data.get("customer", "")
        posting_date_str = event_data.get("posting_date", "")
        due_date_str = event_data.get("due_date")

        posting_date = (
            date.fromisoformat(posting_date_str[:10])
            if posting_date_str
            else datetime.now(tz=UTC).date()
        )

        # BR-ACCT-005: 음수 금액(반품) 시 차대변 역전
        accounts = _build_sales_accounts(grand_total, net_total, tax_amount, customer)

        je_id = self._create_journal_entry(
            voucher_type="sales_invoice",
            voucher_no=doc_id,
            posting_date=posting_date,
            accounts=accounts,
            remark=f"매출전표 자동 분개: {doc_id}",
        )

        # AR 레코드 생성
        ar_id = generate_name("AREC", tenant_id=self._tenant_id)
        due_date = date.fromisoformat(due_date_str[:10]) if due_date_str else None
        ar_doc = AccountsReceivable(
            _id=ar_id,
            tenant_id=self._tenant_id,
            customer=customer,
            outstanding_amount=grand_total,
            due_date=due_date,
            invoice_id=doc_id,
        )
        self._ar_repo.insert(ar_doc)

        return je_id

    def create_purchase_invoice_journal(self, purchase_invoice_id: str) -> str:
        """BR-ACCT-006: 매입전표 분개를 생성한다.

        차변: 재고자산 = net_total
        차변: 부가세대급금 = tax_total (있을 때만)
        대변: 매입채무(AP) = grand_total
        """
        pi_repo = Repository("purchase_invoices", tenant_id=self._tenant_id)
        pi_doc = pi_repo.find_by_id(purchase_invoice_id)
        if not pi_doc:
            raise_not_found(f"매입전표를 찾을 수 없습니다: {purchase_invoice_id}")

        grand_total = _to_decimal(pi_doc.get("grand_total", 0))
        # BR-ACCT-006: grand_total=0이면 분개를 생성하지 않는다
        if grand_total == 0:
            logger.info("grand_total=0이므로 분개를 생성하지 않습니다: %s", purchase_invoice_id)
            return ""
        net_total = _to_decimal(pi_doc.get("net_total", 0))
        tax_total = _to_decimal(pi_doc.get("tax_total", 0))
        supplier = pi_doc.get("supplier", "")
        posting_date_raw = pi_doc.get("posting_date", datetime.now(tz=UTC).date())
        posting_date = (
            posting_date_raw.date() if hasattr(posting_date_raw, "date") else posting_date_raw
        )

        accounts: list[dict[str, Any]] = [
            {
                "account": "재고자산",
                "account_type": "asset",
                "debit": net_total,
                "credit": Decimal(0),
            },
        ]
        if tax_total > 0:
            accounts.append(
                {
                    "account": "부가세대급금",
                    "account_type": "asset",
                    "debit": tax_total,
                    "credit": Decimal(0),
                },
            )
        accounts.append(
            {
                "account": "매입채무",
                "account_type": "liability",
                "debit": Decimal(0),
                "credit": grand_total,
                "party": supplier,
            },
        )

        je_id = self._create_journal_entry(
            voucher_type="purchase_invoice",
            voucher_no=purchase_invoice_id,
            posting_date=posting_date,
            accounts=accounts,
            remark=f"매입전표 자동 분개: {purchase_invoice_id}",
        )

        # AP 레코드 생성
        ap_id = generate_name("AP", tenant_id=self._tenant_id)
        ap_doc = AccountsPayable(
            _id=ap_id,
            tenant_id=self._tenant_id,
            supplier=supplier,
            supplier_name=str(pi_doc.get("supplier_name", "") or supplier),
            outstanding_amount=grand_total,
            due_date=pi_doc.get("due_date"),
            invoice_id=purchase_invoice_id,
        )
        self._ap_repo.insert(ap_doc)

        return je_id

    def create_purchase_invoice_journal_from_event(self, event_data: dict[str, Any]) -> str:
        """BR-ACCT-006: 이벤트 데이터에서 직접 매입 분개를 생성한다.

        차변: 재고자산 = net_total
        차변: 부가세대급금 = tax_total (있을 때만)
        대변: 매입채무(AP) = grand_total
        """
        doc_id = event_data.get("doc_id", "")
        grand_total = _to_decimal(event_data.get("grand_total", 0))
        # BR-ACCT-006: grand_total=0이면 분개를 생성하지 않는다
        if grand_total == 0:
            logger.info("grand_total=0이므로 분개를 생성하지 않습니다: %s", doc_id)
            return ""
        tax_total = _to_decimal(event_data.get("tax_total", 0))
        # net_total이 없으면 grand_total - tax_total로 계산
        net_total_raw = event_data.get("net_total", 0)
        net_total = _to_decimal(net_total_raw) if net_total_raw else grand_total - tax_total
        supplier = event_data.get("supplier", "")
        posting_date_str = event_data.get("posting_date", "")
        due_date_str = event_data.get("due_date")

        posting_date = (
            date.fromisoformat(posting_date_str[:10])
            if posting_date_str
            else datetime.now(tz=UTC).date()
        )

        accounts: list[dict[str, Any]] = [
            {
                "account": "재고자산",
                "account_type": "asset",
                "debit": net_total,
                "credit": Decimal(0),
            },
        ]
        if tax_total > 0:
            accounts.append(
                {
                    "account": "부가세대급금",
                    "account_type": "asset",
                    "debit": tax_total,
                    "credit": Decimal(0),
                },
            )
        accounts.append(
            {
                "account": "매입채무",
                "account_type": "liability",
                "debit": Decimal(0),
                "credit": grand_total,
                "party": supplier,
            },
        )

        je_id = self._create_journal_entry(
            voucher_type="purchase_invoice",
            voucher_no=doc_id,
            posting_date=posting_date,
            accounts=accounts,
            remark=f"매입전표 자동 분개: {doc_id}",
        )

        # AP 레코드 생성
        ap_id = generate_name("AP", tenant_id=self._tenant_id)
        due_date = date.fromisoformat(due_date_str[:10]) if due_date_str else None
        ap_doc = AccountsPayable(
            _id=ap_id,
            tenant_id=self._tenant_id,
            supplier=supplier,
            supplier_name=str(event_data.get("supplier_name", "") or supplier),
            outstanding_amount=grand_total,
            due_date=due_date,
            invoice_id=doc_id,
        )
        self._ap_repo.insert(ap_doc)

        return je_id

    def create_payment_journal(self, payment_entry_id: str) -> str:
        """BR-ACCT-007/008: 수금/지급 분개를 생성한다.

        receive(수금): 차변(은행), 대변(매출채권) + AR outstanding 차감
        pay(지급): 차변(매입채무), 대변(은행) + AP outstanding 차감
        """
        pe_repo = Repository("payment_entries", tenant_id=self._tenant_id)
        pe_doc = pe_repo.find_by_id(payment_entry_id)
        if not pe_doc:
            raise_not_found(f"입금/출금 전표를 찾을 수 없습니다: {payment_entry_id}")

        payment_type = pe_doc.get("payment_type", "").lower()
        amount = _to_decimal(pe_doc.get("paid_amount", 0))
        posting_date_raw = pe_doc.get("posting_date", datetime.now(tz=UTC).date())
        posting_date = (
            posting_date_raw.date() if hasattr(posting_date_raw, "date") else posting_date_raw
        )
        # reference_name(E2E 호환) → reference_no 폴백
        reference_no = pe_doc.get("reference_name", "") or pe_doc.get("reference_no", "")

        if payment_type == "receive":
            # BR-ACCT-007: 수금 — 차변(은행), 대변(매출채권)
            party = pe_doc.get("party_id", "") or pe_doc.get("party", "")
            accounts: list[dict[str, Any]] = [
                {
                    "account": "은행",
                    "account_type": "asset",
                    "debit": amount,
                    "credit": Decimal(0),
                },
                {
                    "account": "매출채권",
                    "account_type": "asset",
                    "debit": Decimal(0),
                    "credit": amount,
                    "party": party,
                },
            ]
            remark = f"수금 분개: {payment_entry_id}"
            # AR outstanding 차감
            if reference_no:
                self._reduce_outstanding(self._ar_repo, reference_no, amount)
        else:
            # BR-ACCT-008: 지급 — 차변(매입채무), 대변(은행)
            party = pe_doc.get("party_id", "") or pe_doc.get("party", "")
            accounts = [
                {
                    "account": "매입채무",
                    "account_type": "liability",
                    "debit": amount,
                    "credit": Decimal(0),
                    "party": party,
                },
                {
                    "account": "은행",
                    "account_type": "asset",
                    "debit": Decimal(0),
                    "credit": amount,
                },
            ]
            remark = f"지급 분개: {payment_entry_id}"
            # AP outstanding 차감
            if reference_no:
                self._reduce_outstanding(self._ap_repo, reference_no, amount)

        return self._create_journal_entry(
            voucher_type="payment_entry",
            voucher_no=payment_entry_id,
            posting_date=posting_date,
            accounts=accounts,
            remark=remark,
        )

    def create_expense_claim_journal_from_event(self, event_data: dict[str, Any]) -> str:
        """BR-ACCT-009: 이벤트 데이터에서 직접 경비 분개를 생성한다.

        차변: 판관비-경비 = total_amount
        대변: 미지급금 = total_amount
        """
        doc_id = event_data.get("doc_id", "")
        total_amount = _to_decimal(event_data.get("total_amount", 0))
        posting_date_str = event_data.get("posting_date", "")

        posting_date = (
            date.fromisoformat(posting_date_str[:10])
            if posting_date_str
            else datetime.now(tz=UTC).date()
        )

        accounts: list[dict[str, Any]] = [
            {
                "account": "판관비-경비",
                "account_type": "expense",
                "debit": total_amount,
                "credit": Decimal(0),
            },
            {
                "account": "미지급금",
                "account_type": "liability",
                "debit": Decimal(0),
                "credit": total_amount,
            },
        ]

        return self._create_journal_entry(
            voucher_type="expense_claim",
            voucher_no=doc_id,
            posting_date=posting_date,
            accounts=accounts,
            remark=f"경비 청구 자동 분개: {doc_id}",
        )

    def create_payroll_journal_from_event(self, event_data: dict[str, Any]) -> str:
        """BR-ACCT-010: 이벤트 데이터에서 직접 급여 분개를 생성한다 (6계정).

        차변: 급여 = total_gross, 복리후생비-4대보험(사업주) = total_employer_insurance
        대변: 미지급급여 = total_net, 예수금-4대보험, 예수금-소득세, 예수금-지방소득세,
              미지급비용-4대보험(사업주 부담분)
        """
        doc_id = event_data.get("doc_id", "")
        total_gross = _to_decimal(event_data.get("total_gross", 0))
        total_net = _to_decimal(event_data.get("total_net", 0))
        total_employee_insurance = _to_decimal(event_data.get("total_employee_insurance", 0))
        total_employer_insurance = _to_decimal(event_data.get("total_employer_insurance", 0))
        total_income_tax = _to_decimal(event_data.get("total_income_tax", 0))
        total_local_income_tax = _to_decimal(event_data.get("total_local_income_tax", 0))
        posting_date_str = event_data.get("posting_date", "")

        posting_date = (
            date.fromisoformat(posting_date_str[:10])
            if posting_date_str
            else datetime.now(tz=UTC).date()
        )

        # 차변
        accounts: list[dict[str, Any]] = [
            {
                "account": "급여",
                "account_type": "expense",
                "debit": total_gross,
                "credit": Decimal(0),
            },
        ]
        if total_employer_insurance > 0:
            accounts.append(
                {
                    "account": "복리후생비-4대보험",
                    "account_type": "expense",
                    "debit": total_employer_insurance,
                    "credit": Decimal(0),
                },
            )

        # 대변
        accounts.append(
            {
                "account": "미지급급여",
                "account_type": "liability",
                "debit": Decimal(0),
                "credit": total_net,
            }
        )
        if total_employee_insurance > 0:
            accounts.append(
                {
                    "account": "예수금-4대보험",
                    "account_type": "liability",
                    "debit": Decimal(0),
                    "credit": total_employee_insurance,
                },
            )
        if total_income_tax > 0:
            accounts.append(
                {
                    "account": "예수금-소득세",
                    "account_type": "liability",
                    "debit": Decimal(0),
                    "credit": total_income_tax,
                },
            )
        if total_local_income_tax > 0:
            accounts.append(
                {
                    "account": "예수금-지방소득세",
                    "account_type": "liability",
                    "debit": Decimal(0),
                    "credit": total_local_income_tax,
                },
            )
        if total_employer_insurance > 0:
            accounts.append(
                {
                    "account": "미지급비용-4대보험",
                    "account_type": "liability",
                    "debit": Decimal(0),
                    "credit": total_employer_insurance,
                },
            )

        return self._create_journal_entry(
            voucher_type="payroll_entry",
            voucher_no=doc_id,
            posting_date=posting_date,
            accounts=accounts,
            remark=f"급여 자동 분개: {doc_id}",
        )

    @staticmethod
    def _reduce_outstanding(repo: Repository, voucher_no: str, amount: Decimal) -> None:
        """AR/AP의 outstanding_amount를 차감한다.

        BR-ACCT-013: 0 미만으로 내려가지 않도록 보호한다.
        """
        docs = repo.find_many({"invoice_id": voucher_no}, limit=1)
        if not docs:
            logger.warning("outstanding 차감 대상 문서 없음: %s", voucher_no)
            return

        doc = docs[0]
        current = _to_decimal(doc.get("outstanding_amount", 0))
        new_amount = max(current - amount, Decimal(0))
        repo.update_by_id(doc["_id"], {"outstanding_amount": new_amount})
