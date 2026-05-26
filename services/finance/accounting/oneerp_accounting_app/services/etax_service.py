"""전자세금계산서 처리 서비스 — 국세청 API 연동 비즈니스 로직.

L2 비즈니스 룰 매핑:
- BR-KTAX-001: 전자세금계산서 발행 의무 (부가가치세법 제32조)
- BR-KTAX-002: 필수 기재사항 (공급자/수요자 사업자번호, 공급가액, 부가세액, 작성일자)
- BR-KTAX-013: 사업자등록번호 형식/체크디짓 검증 (validate_brn)
- BR-KTAX-015: 국세청 전송 재시도 (이벤트 큐 수준, 최대 3회 지수 백오프)
- BR-KTAX-017: 취소 기한 검증 (발급일로부터 익월 10일 이전만)
- BR-KTAX-020: XML K-EC 표준 변환
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Any, cast
from xml.etree.ElementTree import Element, SubElement, tostring

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.repository import Repository

if TYPE_CHECKING:
    from .nts_api_client import NTSApiClient

logger = logging.getLogger(__name__)

_COLLECTION = "etax_invoices"

# BR-KTAX-013: 사업자등록번호 체크디짓 가중치
_BRN_WEIGHTS = (1, 3, 7, 1, 3, 7, 1, 3, 5)


def validate_brn(brn: str) -> bool:
    """BR-KTAX-013: 사업자등록번호 형식 및 체크디짓을 검증한다.

    형식: XXX-XX-XXXXX (10자리 숫자). 하이픈 있/없 모두 허용.
    체크디짓: 가중치 곱 합산 → 마지막 자리 검증.

    Returns:
        유효하면 True, 아니면 False
    """
    digits = brn.replace("-", "")
    if len(digits) != 10 or not digits.isdigit():
        return False

    total = sum(int(digits[i]) * _BRN_WEIGHTS[i] for i in range(9))
    total += (int(digits[8]) * 5) // 10
    check = (10 - (total % 10)) % 10
    return check == int(digits[9])


class ETaxServiceError(Exception):
    """전자세금계산서 처리 중 발생하는 비즈니스 에러."""


def _cancel_deadline(issue_date: date) -> date:
    """BR-KTAX-017: 취소 기한을 계산한다 (발급일 익월 10일)."""
    if issue_date.month == 12:
        return date(issue_date.year + 1, 1, 10)
    return date(issue_date.year, issue_date.month + 1, 10)


class ETaxService:
    """전자세금계산서 처리 서비스.

    국세청 API 클라이언트를 이용하여 전자세금계산서를
    전송/조회/취소하는 비즈니스 로직을 캡슐화한다.
    """

    def __init__(self, nts_client: NTSApiClient, tenant_id: str) -> None:
        self._nts_client = nts_client
        self._tenant_id = tenant_id
        self._repo = Repository(_COLLECTION, tenant_id=tenant_id)

    def _find_invoice(self, doc_id: str) -> dict[str, Any]:
        """전자세금계산서를 조회한다. 미존재 시 에러를 발생시킨다."""
        doc = self._repo.find_by_id(doc_id)
        if not doc:
            raise_not_found(f"전자세금계산서를 찾을 수 없습니다: {doc_id}")
        return cast("dict[str, Any]", doc)

    @staticmethod
    def _build_xml_payload(doc: dict[str, Any]) -> str:
        """BR-KTAX-020: 전자세금계산서 데이터를 K-EC 표준 XML로 변환한다."""
        root = Element("TaxInvoice")
        root.set(
            "xmlns",
            "urn:kr:or:kec:standard:Tax:ReusableAggregateBusinessInformationEntitySchemaModule:1:0",
        )

        # 발급 정보
        exchange_doc = SubElement(root, "ExchangedDocument")
        issue_id = SubElement(exchange_doc, "IssueID")
        issue_id.text = doc.get("_id", "")
        issue_date_elem = SubElement(exchange_doc, "IssueDateTime")
        issue_date_val = doc.get("issue_date")
        if issue_date_val:
            issue_date_elem.text = str(issue_date_val)

        # 공급자/수요자 정보
        trade_party = SubElement(root, "TradeSettlement")
        party_name = SubElement(trade_party, "SupplierOrCustomer")
        party_name.text = doc.get("supplier_or_customer", "")

        # 금액 정보
        monetary = SubElement(root, "MonetarySummation")
        supply_elem = SubElement(monetary, "SupplyAmount")
        supply_elem.text = str(doc.get("supply_amount", 0))
        tax_elem = SubElement(monetary, "TaxAmount")
        tax_elem.text = str(doc.get("tax_amount", 0))

        # 발행유형/영수청구 구분
        type_elem = SubElement(root, "IssueType")
        type_elem.text = doc.get("issue_type", "정발행")
        receipt_elem = SubElement(root, "ReceiptType")
        receipt_elem.text = doc.get("receipt_type", "청구")

        return tostring(root, encoding="unicode", xml_declaration=True)

    async def submit_to_nts(self, doc_id: str) -> dict[str, Any]:
        """전자세금계산서를 국세청에 전송한다.

        Raises:
            OneERPError(ERR-KTAX-030): 미제출 문서 전송 시도
        """
        doc = self._find_invoice(doc_id)

        # 이미 전송된 문서 검증
        if doc.get("transmission_status") == "sent":
            raise_unprocessable(
                "ERR-KTAX-030",
                f"이미 국세청에 전송된 문서입니다: {doc_id}",
            )

        # XML 페이로드 생성
        xml_payload = self._build_xml_payload(doc)

        # 국세청 API 호출
        invoice_data = {
            "xml_payload": xml_payload,
            "doc_id": doc_id,
            "tenant_id": self._tenant_id,
        }
        nts_response = await self._nts_client.submit_invoice(invoice_data)

        # DB 업데이트
        now = datetime.now(tz=UTC)
        update_data = {
            "transmission_status": "sent",
            "nts_confirmation_no": nts_response.get("confirmation_no"),
            "nts_submitted_at": now,
            "xml_payload": xml_payload,
            "nts_response": nts_response,
        }
        self._repo.update_by_id(doc_id, update_data)

        logger.info(
            "국세청 전송 완료: doc_id=%s, confirmation_no=%s",
            doc_id,
            nts_response.get("confirmation_no"),
        )
        return {
            "doc_id": doc_id,
            "transmission_status": "sent",
            "nts_confirmation_no": nts_response.get("confirmation_no"),
            "nts_submitted_at": now.isoformat(),
        }

    async def check_nts_status(self, doc_id: str) -> dict[str, Any]:
        """국세청 전송 상태를 조회한다."""
        doc = self._find_invoice(doc_id)

        confirmation_no = doc.get("nts_confirmation_no")
        if not confirmation_no:
            raise_unprocessable(
                "ERR-KTAX-030",
                f"국세청 승인번호가 없습니다: {doc_id}",
            )
        confirmation_no = str(confirmation_no)

        nts_response = await self._nts_client.check_status(confirmation_no)

        if nts_response.get("status") == "confirmed":
            now = datetime.now(tz=UTC)
            self._repo.update_by_id(
                doc_id,
                {
                    "transmission_status": "confirmed",
                    "nts_confirmed_at": now,
                    "nts_response": nts_response,
                },
            )

        logger.info(
            "국세청 상태 조회: doc_id=%s, status=%s",
            doc_id,
            nts_response.get("status"),
        )
        return {
            "doc_id": doc_id,
            "confirmation_no": confirmation_no,
            "nts_status": nts_response.get("status"),
        }

    async def cancel_nts(self, doc_id: str, reason: str) -> dict[str, Any]:
        """국세청 전송을 취소한다.

        BR-KTAX-017: 발급일로부터 익월 10일 이전만 취소 가능.

        Raises:
            OneERPError(ERR-KTAX-031): 취소 기한 초과
        """
        doc = self._find_invoice(doc_id)

        confirmation_no = doc.get("nts_confirmation_no")
        if not confirmation_no:
            raise_unprocessable(
                "ERR-KTAX-030",
                f"국세청 승인번호가 없습니다: {doc_id}",
            )
        confirmation_no = str(confirmation_no)

        # BR-KTAX-017: 취소 기한 검증
        issue_date = doc.get("issue_date")
        if issue_date:
            if isinstance(issue_date, str):
                issue_date = date.fromisoformat(issue_date[:10])
            elif isinstance(issue_date, datetime):
                issue_date = issue_date.date()
            deadline = _cancel_deadline(issue_date)
            today = datetime.now(tz=UTC).date()
            if today > deadline:
                raise_unprocessable(
                    "ERR-KTAX-031",
                    f"취소 기한이 초과되었습니다 (발급일: {issue_date}, 기한: {deadline})",
                )

        # 국세청 API 호출
        nts_response = await self._nts_client.cancel_invoice(confirmation_no, reason)

        # DB 업데이트
        self._repo.update_by_id(
            doc_id,
            {
                "transmission_status": "cancelled",
                "nts_response": nts_response,
            },
        )

        logger.info(
            "국세청 취소 완료: doc_id=%s, confirmation_no=%s, reason=%s",
            doc_id,
            confirmation_no,
            reason,
        )
        return {
            "doc_id": doc_id,
            "confirmation_no": confirmation_no,
            "nts_status": "cancelled",
        }
