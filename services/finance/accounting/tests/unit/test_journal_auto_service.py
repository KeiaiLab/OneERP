"""자동 분개 서비스(JournalAutoService) 단위 테스트."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


@pytest.fixture(autouse=True)
def _mock_generate_name():
    """generate_name을 테스트 전체 기간 동안 모킹한다."""
    _counter: dict[str, int] = {}

    def _gen(prefix: str, *, tenant_id: str | None = None) -> str:
        _counter[prefix] = _counter.get(prefix, 0) + 1
        return f"{prefix}-2026-{_counter[prefix]:05d}"

    with patch(
        "oneerp_accounting_app.services.journal_auto_service.generate_name",
        side_effect=_gen,
    ):
        yield


@pytest.fixture
def service_and_repos():
    """JournalAutoService와 모킹된 Repository 딕셔너리를 반환한다.

    패치를 fixture 스코프로 유지하여 메서드 호출 시에도 Repository가 모킹된다.
    """
    with patch("oneerp_accounting_app.services.journal_auto_service.Repository") as mock_repo_cls:
        repos: defaultdict[str, MagicMock] = defaultdict(MagicMock)

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            return repos[collection_name]

        mock_repo_cls.side_effect = _repo_factory

        from oneerp_accounting_app.services.journal_auto_service import JournalAutoService

        service = JournalAutoService(tenant_id="test-tenant")

        yield service, repos


class Test매출전표분개:
    """create_sales_invoice_journal 테스트."""

    def test_매출전표_분개_차대변일치(self, service_and_repos: tuple) -> None:
        """매출전표에서 생성된 분개의 차변/대변 합계가 일치한다."""
        service, repos = service_and_repos
        si_repo = repos["sales_invoices"]
        si_repo.find_by_id.return_value = {
            "_id": "SI-001",
            "grand_total": 110000.0,
            "net_total": 100000.0,
            "customer": "CUST-001",
            "posting_date": date(2026, 3, 1),
            "due_date": date(2026, 4, 1),
        }

        je_id = service.create_sales_invoice_journal("SI-001")

        assert je_id.startswith("JE-")
        # JE 삽입 호출 확인
        je_repo = repos["journal_entries"]
        je_repo.insert.assert_called_once()
        je_doc = je_repo.insert.call_args[0][0]
        assert je_doc.total_debit == je_doc.total_credit == 110000.0
        assert je_doc.docstatus == 1  # 즉시 제출

    def test_매출전표_부가세_분리(self, service_and_repos: tuple) -> None:
        """세액이 있으면 부가세예수금 대변 항목이 분리 생성된다."""
        service, repos = service_and_repos
        si_repo = repos["sales_invoices"]
        si_repo.find_by_id.return_value = {
            "_id": "SI-002",
            "grand_total": 110000.0,
            "net_total": 100000.0,
            "customer": "CUST-001",
            "posting_date": date(2026, 3, 1),
        }

        service.create_sales_invoice_journal("SI-002")

        je_repo = repos["journal_entries"]
        je_doc = je_repo.insert.call_args[0][0]
        accounts = {item.account: item for item in je_doc.items}
        assert "매출채권" in accounts
        assert accounts["매출채권"].debit == 110000.0
        assert "매출" in accounts
        assert accounts["매출"].credit == 100000.0
        assert "부가세예수금" in accounts
        assert accounts["부가세예수금"].credit == 10000.0

    def test_매출전표_세액없음(self, service_and_repos: tuple) -> None:
        """세액이 없으면 부가세예수금 항목이 생성되지 않는다."""
        service, repos = service_and_repos
        si_repo = repos["sales_invoices"]
        si_repo.find_by_id.return_value = {
            "_id": "SI-003",
            "grand_total": 100000.0,
            "net_total": 100000.0,
            "customer": "CUST-001",
            "posting_date": date(2026, 3, 1),
        }

        service.create_sales_invoice_journal("SI-003")

        je_repo = repos["journal_entries"]
        je_doc = je_repo.insert.call_args[0][0]
        account_names = {item.account for item in je_doc.items}
        assert "부가세예수금" not in account_names

    def test_매출전표_AR_생성(self, service_and_repos: tuple) -> None:
        """매출전표 분개 시 매출채권(AR) 레코드가 생성된다."""
        service, repos = service_and_repos
        si_repo = repos["sales_invoices"]
        si_repo.find_by_id.return_value = {
            "_id": "SI-004",
            "grand_total": 55000.0,
            "net_total": 50000.0,
            "customer": "CUST-002",
            "posting_date": date(2026, 3, 1),
            "due_date": date(2026, 4, 1),
        }

        service.create_sales_invoice_journal("SI-004")

        ar_repo = repos["accounts_receivable"]
        ar_repo.insert.assert_called_once()
        ar_doc = ar_repo.insert.call_args[0][0]
        assert ar_doc.customer == "CUST-002"
        assert ar_doc.outstanding_amount == 55000.0
        assert ar_doc.invoice_id == "SI-004"


class Test매입전표분개:
    """create_purchase_invoice_journal 테스트."""

    def test_매입전표_분개_AP_생성(self, service_and_repos: tuple) -> None:
        """매입전표 분개 시 매입채무(AP) 레코드가 생성된다."""
        service, repos = service_and_repos
        pi_repo = repos["purchase_invoices"]
        pi_repo.find_by_id.return_value = {
            "_id": "PI-001",
            "grand_total": 220000.0,
            "net_total": 200000.0,
            "tax_total": 20000.0,
            "supplier": "SUP-001",
            "supplier_name": "테스트 공급업체",
            "posting_date": date(2026, 3, 1),
            "due_date": date(2026, 4, 1),
        }

        je_id = service.create_purchase_invoice_journal("PI-001")

        assert je_id.startswith("JE-")
        # 분개 차대변 검증
        je_repo = repos["journal_entries"]
        je_doc = je_repo.insert.call_args[0][0]
        assert je_doc.total_debit == je_doc.total_credit == 220000.0

        accounts = {item.account: item for item in je_doc.items}
        assert accounts["재고자산"].debit == 200000.0
        assert accounts["부가세대급금"].debit == 20000.0
        assert accounts["매입채무"].credit == 220000.0

        # AP 레코드 검증
        ap_repo = repos["accounts_payable"]
        ap_repo.insert.assert_called_once()
        ap_doc = ap_repo.insert.call_args[0][0]
        assert ap_doc.supplier == "SUP-001"
        assert ap_doc.supplier_name == "테스트 공급업체"
        assert ap_doc.outstanding_amount == 220000.0

    def test_매입전표_세액없음(self, service_and_repos: tuple) -> None:
        """세액이 없으면 부가세대급금 항목이 생성되지 않는다."""
        service, repos = service_and_repos
        pi_repo = repos["purchase_invoices"]
        pi_repo.find_by_id.return_value = {
            "_id": "PI-002",
            "grand_total": 100000.0,
            "net_total": 100000.0,
            "tax_total": 0.0,
            "supplier": "SUP-002",
            "posting_date": date(2026, 3, 1),
        }

        service.create_purchase_invoice_journal("PI-002")

        je_repo = repos["journal_entries"]
        je_doc = je_repo.insert.call_args[0][0]
        account_names = {item.account for item in je_doc.items}
        assert "부가세대급금" not in account_names


class Test수금지급분개:
    """create_payment_journal 테스트."""

    def test_수금_분개_AR_잔액차감(self, service_and_repos: tuple) -> None:
        """수금 분개 시 AR outstanding_amount가 차감된다."""
        service, repos = service_and_repos
        pe_repo = repos["payment_entries"]
        pe_repo.find_by_id.return_value = {
            "_id": "PE-001",
            "payment_type": "Receive",
            "paid_amount": 50000.0,
            "party": "CUST-001",
            "posting_date": date(2026, 3, 15),
            "reference_no": "SI-001",
        }

        ar_repo = repos["accounts_receivable"]
        ar_repo.find_many.return_value = [
            {"_id": "AREC-001", "outstanding_amount": 110000.0, "invoice_id": "SI-001"},
        ]

        je_id = service.create_payment_journal("PE-001")

        assert je_id.startswith("JE-")
        je_repo = repos["journal_entries"]
        je_doc = je_repo.insert.call_args[0][0]
        accounts = {item.account: item for item in je_doc.items}
        assert accounts["은행"].debit == 50000.0
        assert accounts["매출채권"].credit == 50000.0

        # AR 잔액 차감
        ar_repo.update_by_id.assert_called_once_with(
            "AREC-001",
            {"outstanding_amount": 60000.0},
        )

    def test_지급_분개_AP_잔액차감(self, service_and_repos: tuple) -> None:
        """지급 분개 시 AP outstanding_amount가 차감된다."""
        service, repos = service_and_repos
        pe_repo = repos["payment_entries"]
        pe_repo.find_by_id.return_value = {
            "_id": "PE-002",
            "payment_type": "Pay",
            "paid_amount": 100000.0,
            "party": "SUP-001",
            "posting_date": date(2026, 3, 15),
            "reference_no": "PI-001",
        }

        ap_repo = repos["accounts_payable"]
        ap_repo.find_many.return_value = [
            {"_id": "AP-001", "outstanding_amount": 220000.0, "invoice_id": "PI-001"},
        ]

        je_id = service.create_payment_journal("PE-002")

        assert je_id.startswith("JE-")
        je_repo = repos["journal_entries"]
        je_doc = je_repo.insert.call_args[0][0]
        accounts = {item.account: item for item in je_doc.items}
        assert accounts["매입채무"].debit == 100000.0
        assert accounts["은행"].credit == 100000.0

        # AP 잔액 차감
        ap_repo.update_by_id.assert_called_once_with(
            "AP-001",
            {"outstanding_amount": 120000.0},
        )


class Test경비분개:
    """create_expense_claim_journal_from_event 테스트."""

    def test_경비_분개_미지급금(self, service_and_repos: tuple) -> None:
        """경비 청구 이벤트 데이터로 판관비-경비(차변)와 미지급금(대변) 분개가 생성된다."""
        service, repos = service_and_repos

        event_data = {
            "doc_id": "EC-001",
            "total_amount": 350000.0,
            "posting_date": "2026-03-10",
        }

        je_id = service.create_expense_claim_journal_from_event(event_data)

        assert je_id.startswith("JE-")
        je_repo = repos["journal_entries"]
        je_doc = je_repo.insert.call_args[0][0]
        assert je_doc.total_debit == je_doc.total_credit == 350000.0

        accounts = {item.account: item for item in je_doc.items}
        assert accounts["판관비-경비"].debit == 350000.0
        assert accounts["미지급금"].credit == 350000.0


class Test급여분개:
    """create_payroll_journal_from_event 테스트."""

    def test_급여_분개_예수금_분리(self, service_and_repos: tuple) -> None:
        """급여 이벤트 데이터로 4대보험, 소득세, 지방소득세가 예수금으로 분리된다."""
        service, repos = service_and_repos

        # payroll 서비스가 이벤트에 합산 데이터를 포함하여 발행
        event_data = {
            "doc_id": "PR-001",
            "posting_date": "2026-03-25",
            "total_gross": 9000000.0,
            "total_net": 7398000.0,
            "total_employee_insurance": 810000.0,
            "total_employer_insurance": 900000.0,
            "total_income_tax": 720000.0,
            "total_local_income_tax": 72000.0,
        }

        je_id = service.create_payroll_journal_from_event(event_data)

        assert je_id.startswith("JE-")
        je_repo = repos["journal_entries"]
        je_doc = je_repo.insert.call_args[0][0]

        # 차변: 급여(9,000,000) + 복리후생비-4대보험(900,000) = 9,900,000
        # 대변: 미지급급여(7,398,000) + 예수금-4대보험(810,000) + 예수금-소득세(720,000)
        #       + 예수금-지방소득세(72,000) + 미지급비용-4대보험(900,000) = 9,900,000
        assert je_doc.total_debit == je_doc.total_credit == 9900000.0

        accounts = {item.account: item for item in je_doc.items}
        assert accounts["급여"].debit == 9000000.0
        assert accounts["복리후생비-4대보험"].debit == 900000.0
        assert accounts["미지급급여"].credit == 7398000.0
        assert accounts["예수금-4대보험"].credit == 810000.0
        assert accounts["예수금-소득세"].credit == 720000.0
        assert accounts["예수금-지방소득세"].credit == 72000.0
        assert accounts["미지급비용-4대보험"].credit == 900000.0


class TestAR_outstanding_하한:
    """BR-ACCT-013: AR outstanding이 0 미만으로 내려가지 않는다."""

    def test_초과수금시_outstanding_0으로_고정(self, service_and_repos: tuple) -> None:
        """BR-ACCT-013: 수금액이 outstanding보다 크면 0으로 고정된다."""
        service, repos = service_and_repos
        pe_repo = repos["payment_entries"]
        pe_repo.find_by_id.return_value = {
            "_id": "PE-OVER",
            "payment_type": "Receive",
            "paid_amount": 200000.0,  # outstanding(100000)보다 큼
            "party": "CUST-001",
            "posting_date": date(2026, 3, 15),
            "reference_no": "SI-OVER",
        }
        ar_repo = repos["accounts_receivable"]
        ar_repo.find_many.return_value = [
            {"_id": "AREC-OVER", "outstanding_amount": 100000.0, "invoice_id": "SI-OVER"},
        ]

        service.create_payment_journal("PE-OVER")

        # BR-ACCT-013: outstanding = max(100000 - 200000, 0) = 0
        ar_repo.update_by_id.assert_called_once_with(
            "AREC-OVER",
            {"outstanding_amount": Decimal(0)},
        )

    def test_정확히_동일금액_수금시_outstanding_0(self, service_and_repos: tuple) -> None:
        """BR-ACCT-013: 경계값 — 정확히 동일 금액 수금 시 outstanding = 0."""
        service, repos = service_and_repos
        pe_repo = repos["payment_entries"]
        pe_repo.find_by_id.return_value = {
            "_id": "PE-EXACT",
            "payment_type": "Receive",
            "paid_amount": 55000.0,
            "party": "CUST-001",
            "posting_date": date(2026, 3, 15),
            "reference_no": "SI-EXACT",
        }
        ar_repo = repos["accounts_receivable"]
        ar_repo.find_many.return_value = [
            {"_id": "AREC-EXACT", "outstanding_amount": 55000.0, "invoice_id": "SI-EXACT"},
        ]

        service.create_payment_journal("PE-EXACT")

        ar_repo.update_by_id.assert_called_once_with(
            "AREC-EXACT",
            {"outstanding_amount": Decimal(0)},
        )

    def test_reference_no_없으면_AR_차감_생략(self, service_and_repos: tuple) -> None:
        """BR-ACCT-007: reference_no가 없으면 AR outstanding 차감을 생략한다."""
        service, repos = service_and_repos
        pe_repo = repos["payment_entries"]
        pe_repo.find_by_id.return_value = {
            "_id": "PE-NOREF",
            "payment_type": "Receive",
            "paid_amount": 50000.0,
            "party": "CUST-001",
            "posting_date": date(2026, 3, 15),
            "reference_no": "",  # 비어있음
        }

        service.create_payment_journal("PE-NOREF")

        # AR 조회/갱신이 호출되지 않아야 한다
        ar_repo = repos["accounts_receivable"]
        ar_repo.find_many.assert_not_called()

    def test_지급시_reference_no_없으면_AP_차감_생략(self, service_and_repos: tuple) -> None:
        """BR-ACCT-008: reference_no가 없으면 AP outstanding 차감을 생략한다."""
        service, repos = service_and_repos
        pe_repo = repos["payment_entries"]
        pe_repo.find_by_id.return_value = {
            "_id": "PE-NOREF-PAY",
            "payment_type": "Pay",
            "paid_amount": 80000.0,
            "party": "SUP-001",
            "posting_date": date(2026, 3, 15),
            "reference_no": "",
        }

        service.create_payment_journal("PE-NOREF-PAY")

        ap_repo = repos["accounts_payable"]
        ap_repo.find_many.assert_not_called()


class Test급여_공제0:
    """BR-ACCT-010: 공제 항목이 모두 0인 경우 최소 분개 테스트."""

    def test_공제항목_모두0_최소분개(self, service_and_repos: tuple) -> None:
        """BR-ACCT-010: 공제 0이면 급여(차변)=미지급급여(대변) 2라인만 생성."""
        service, repos = service_and_repos
        event_data = {
            "doc_id": "PR-ZERO",
            "posting_date": "2026-03-25",
            "total_gross": 2000000.0,
            "total_net": 2000000.0,
            "total_employee_insurance": 0.0,
            "total_employer_insurance": 0.0,
            "total_income_tax": 0.0,
            "total_local_income_tax": 0.0,
        }

        service.create_payroll_journal_from_event(event_data)

        je_repo = repos["journal_entries"]
        je_doc = je_repo.insert.call_args[0][0]
        # 차변: 급여 2,000,000 / 대변: 미지급급여 2,000,000
        assert je_doc.total_debit == je_doc.total_credit == 2000000.0
        assert len(je_doc.items) == 2  # 급여 + 미지급급여만
        account_names = {item.account for item in je_doc.items}
        assert "복리후생비-4대보험" not in account_names
        assert "예수금-4대보험" not in account_names


class Test반올림:
    """BR-ACCT-019: 금액 반올림 검증."""

    def test_소수점_반올림_정밀도(self, service_and_repos: tuple) -> None:
        """BR-ACCT-019: 소수점이 있는 금액��� 원 단위로 반올림된다."""
        service, repos = service_and_repos
        si_repo = repos["sales_invoices"]
        si_repo.find_by_id.return_value = {
            "_id": "SI-ROUND",
            "grand_total": 1100.5,  # 반올림 → 1101 (KRW)
            "net_total": 1000.45,  # 반올림 → 1000
            "customer": "CUST-RND",
            "posting_date": date(2026, 3, 1),
        }

        service.create_sales_invoice_journal("SI-ROUND")

        je_repo = repos["journal_entries"]
        je_doc = je_repo.insert.call_args[0][0]
        # _to_decimal은 KRW 원 단위 반올림 (Decimal(1))
        assert je_doc.total_debit == Decimal(1101)
        assert je_doc.total_credit == Decimal(1101)

    def test_영_금액_분개_미생성_방어(self, service_and_repos: tuple) -> None:
        """BR-ACCT-005: grand_total=0이면 분개를 생성하지 않고 빈 문자열을 반환한다."""
        service, repos = service_and_repos
        si_repo = repos["sales_invoices"]
        si_repo.find_by_id.return_value = {
            "_id": "SI-ZERO",
            "grand_total": 0,
            "net_total": 0,
            "customer": "CUST-ZERO",
            "posting_date": date(2026, 3, 1),
        }

        je_id = service.create_sales_invoice_journal("SI-ZERO")

        # grand_total=0이면 분개 미생성, 빈 문자열 반환
        assert je_id == ""
        je_repo = repos["journal_entries"]
        je_repo.insert.assert_not_called()

    def test_영_금액_이벤트_분개_미생성(self, service_and_repos: tuple) -> None:
        """BR-ACCT-005: 이벤트 기반 매출 분개도 grand_total=0이면 생성하지 않는다."""
        service, repos = service_and_repos
        event_data = {
            "doc_id": "SI-ZERO-EVT",
            "grand_total": 0,
            "net_total": 0,
            "customer": "CUST-ZERO",
            "posting_date": "2026-03-01",
        }

        je_id = service.create_sales_invoice_journal_from_event(event_data)

        assert je_id == ""
        je_repo = repos["journal_entries"]
        je_repo.insert.assert_not_called()

    def test_매입전표_영_금액_분개_미생성(self, service_and_repos: tuple) -> None:
        """BR-ACCT-006: 매입전표도 grand_total=0이면 분개를 생성하지 않는다."""
        service, repos = service_and_repos
        pi_repo = repos["purchase_invoices"]
        pi_repo.find_by_id.return_value = {
            "_id": "PI-ZERO",
            "grand_total": 0,
            "net_total": 0,
            "tax_total": 0,
            "supplier": "SUP-ZERO",
            "posting_date": date(2026, 3, 1),
        }

        je_id = service.create_purchase_invoice_journal("PI-ZERO")

        assert je_id == ""
        je_repo = repos["journal_entries"]
        je_repo.insert.assert_not_called()

    def test_매입전표_이벤트_영_금액_분개_미생성(self, service_and_repos: tuple) -> None:
        """BR-ACCT-006: 이벤트 기반 매입 분개도 grand_total=0이면 생성하지 않는다."""
        service, repos = service_and_repos
        event_data = {
            "doc_id": "PI-ZERO-EVT",
            "grand_total": 0,
            "net_total": 0,
            "tax_total": 0,
            "supplier": "SUP-ZERO",
            "posting_date": "2026-03-01",
        }

        je_id = service.create_purchase_invoice_journal_from_event(event_data)

        assert je_id == ""
        je_repo = repos["journal_entries"]
        je_repo.insert.assert_not_called()


class Test반품_차대변역전:
    """BR-ACCT-005: 음수 금액(반품) 시 차대변 역전 검증."""

    def test_반품_매출전표_차대변_역전(self, service_and_repos: tuple) -> None:
        """음수 grand_total 시 매출채권=대변, 매출=차변으로 역전된다."""
        service, repos = service_and_repos
        si_repo = repos["sales_invoices"]
        si_repo.find_by_id.return_value = {
            "_id": "SI-RETURN",
            "grand_total": -110000,
            "net_total": -100000,
            "customer": "CUST-RET",
            "posting_date": date(2026, 3, 1),
        }

        je_id = service.create_sales_invoice_journal("SI-RETURN")

        assert je_id.startswith("JE-")
        je_repo = repos["journal_entries"]
        je_doc = je_repo.insert.call_args[0][0]
        accounts = {item.account: item for item in je_doc.items}
        # 반품: 매출채권 대변, 매출 차변
        assert accounts["매출채권"].credit == Decimal(110000)
        assert accounts["매출채권"].debit == Decimal(0)
        assert accounts["매출"].debit == Decimal(100000)
        assert accounts["매출"].credit == Decimal(0)
        assert accounts["부가세예수금"].debit == Decimal(10000)

    def test_반품_차대변_합계_일치(self, service_and_repos: tuple) -> None:
        """반품 분개도 차변 합계 = 대변 합계를 만족한다."""
        service, repos = service_and_repos
        si_repo = repos["sales_invoices"]
        si_repo.find_by_id.return_value = {
            "_id": "SI-RET2",
            "grand_total": -55000,
            "net_total": -50000,
            "customer": "CUST-RET2",
            "posting_date": date(2026, 3, 1),
        }

        service.create_sales_invoice_journal("SI-RET2")

        je_repo = repos["journal_entries"]
        je_doc = je_repo.insert.call_args[0][0]
        assert je_doc.total_debit == je_doc.total_credit


class Test차대변검증:
    """차대변 불일치 에러 검증."""

    def test_차대변_불일치_에러(self, service_and_repos: tuple) -> None:
        """차변 합계 != 대변 합계일 때 ERR-ACCT-030 에러가 발생한다."""
        service, _repos = service_and_repos

        with pytest.raises(OneERPError, match="ERR-ACCT-030"):
            service._create_journal_entry(
                voucher_type="test",
                voucher_no="TEST-001",
                posting_date=date(2026, 3, 1),
                accounts=[
                    {"account": "현금", "debit": 1000.0, "credit": 0.0},
                    {"account": "매출", "debit": 0.0, "credit": 900.0},  # 100원 부족
                ],
                remark="테스트",
            )

    def test_문서_미존재_에러(self, service_and_repos: tuple) -> None:
        """존재하지 않는 전표 ID로 호출 시 OneERPError(404)가 발생한다."""
        service, repos = service_and_repos
        si_repo = repos["sales_invoices"]
        si_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.create_sales_invoice_journal("NONEXIST-001")

    def test_마감기간_전기_에러(self, service_and_repos: tuple) -> None:
        """EX-ACCT-003: 마감된 회계기간에 분개 생성 시 ERR-ACCT-031 에러."""
        service, repos = service_and_repos
        # 마감된 기간 설정
        period_repo = repos["accounting_periods"]
        period_repo.find_many.return_value = [
            {
                "_id": "APD-001",
                "start_date": date(2026, 1, 1),
                "end_date": date(2026, 1, 31),
                "status": "closed",
            },
        ]

        with pytest.raises(OneERPError, match="ERR-ACCT-031"):
            service._create_journal_entry(
                voucher_type="test",
                voucher_no="TEST-001",
                posting_date=date(2026, 1, 15),
                accounts=[
                    {"account": "현금", "debit": 1000, "credit": 0},
                    {"account": "매출", "debit": 0, "credit": 1000},
                ],
                remark="마감 기간 테스트",
            )

    def test_Decimal_정밀도_보장(self, service_and_repos: tuple) -> None:
        """BR-ACCT-001: 자동 분개 금액이 Decimal로 정확히 계산된다."""
        from decimal import Decimal

        service, repos = service_and_repos
        si_repo = repos["sales_invoices"]
        si_repo.find_by_id.return_value = {
            "_id": "SI-DEC",
            "grand_total": 1100000,
            "net_total": 1000000,
            "customer": "CUST-DEC",
            "posting_date": date(2026, 3, 1),
            "due_date": date(2026, 4, 1),
        }
        # 마감 기간 없음
        period_repo = repos["accounting_periods"]
        period_repo.find_many.return_value = []

        service.create_sales_invoice_journal("SI-DEC")

        # JE 삽입 시 금액이 Decimal인지 확인
        je_repo = repos["journal_entries"]
        inserted = je_repo.insert.call_args[0][0]
        assert isinstance(inserted.total_debit, Decimal)
        assert isinstance(inserted.total_credit, Decimal)
        assert inserted.total_debit == Decimal(1100000)
        assert inserted.total_credit == Decimal(1100000)

    def test_이벤트_outbox_생성(self, service_and_repos: tuple) -> None:
        """자동 분개 생성 시 Outbox 이벤트가 포함된다."""
        service, repos = service_and_repos
        si_repo = repos["sales_invoices"]
        si_repo.find_by_id.return_value = {
            "_id": "SI-EVT",
            "grand_total": 110000,
            "net_total": 100000,
            "customer": "CUST-EVT",
            "posting_date": date(2026, 3, 1),
        }
        period_repo = repos["accounting_periods"]
        period_repo.find_many.return_value = []

        service.create_sales_invoice_journal("SI-EVT")

        je_repo = repos["journal_entries"]
        # insert 후 update_by_id로 outbox 이벤트가 추가된다
        je_repo.insert.assert_called_once()
        je_repo.update_by_id.assert_called_once()
        update_args = je_repo.update_by_id.call_args[0]
        assert "$push" in update_args[1]
        outbox_data = update_args[1]["$push"]["_outbox"]
        assert outbox_data["event_type"] == "journal_entry.submitted"
