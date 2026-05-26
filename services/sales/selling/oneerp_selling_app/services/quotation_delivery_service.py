"""견적서 고객 전달 서비스.

제출된 견적서에 대해 PDF 다운로드, 메일 발송 메타데이터, 포털 전자서명을 처리한다.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any, cast

from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_bad_request, raise_not_found

if TYPE_CHECKING:
    from oneerp_core.repository import Repository


def _coerce_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    return None


def _as_text(value: Any) -> str:
    return str(value).encode("latin-1", "replace").decode("latin-1")


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _decimal_amount(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value or 0))


def _is_submitted_status(docstatus: Any) -> bool:
    return docstatus in {DocStatus.SUBMITTED, "submitted", "Submitted", 1}


def _build_pdf_bytes(lines: list[str]) -> bytes:
    content_lines = ["BT", "/F1 12 Tf", "50 780 Td"]
    for index, line in enumerate(lines):
        if index:
            content_lines.append("0 -18 Td")
        content_lines.append(f"({_escape_pdf_text(_as_text(line))}) Tj")
    content_lines.append("ET")

    stream = "\n".join(content_lines).encode("latin-1")
    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n",
        f"4 0 obj\n<< /Length {len(stream)} >>\nstream\n".encode("latin-1")
        + stream
        + b"\nendstream\nendobj\n",
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]

    pdf = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf += obj

    xref_offset = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n".encode("latin-1")
    pdf += b"0000000000 65535 f \n"
    for offset in offsets[1:]:
        pdf += f"{offset:010d} 00000 n \n".encode("latin-1")
    pdf += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF"
    ).encode("latin-1")
    return pdf


class QuotationDeliveryService:
    """견적서 고객 전달 관련 비즈니스 로직."""

    def __init__(self, repo: Repository, tenant_id: str) -> None:
        self._repo = repo
        self._tenant_id = tenant_id

    def send_email(
        self,
        quotation_id: str,
        *,
        recipient_email: str,
        subject: str,
        message: str,
        actor: str,
    ) -> dict[str, Any]:
        quotation = self._get_submitted_quotation(quotation_id)

        now = datetime.now(tz=UTC)
        token = quotation.get("portal_access_token") or secrets.token_urlsafe(24)
        expires_at = now + timedelta(days=14)
        pdf_file_name = f"{quotation_id}.pdf"
        portal_sign_url = (
            f"/api/v1/portal/quotations/{quotation_id}/sign"
            f"?tenant_id={self._tenant_id}&token={token}"
        )
        pdf_download_url = f"/api/v1/quotations/{quotation_id}/pdf"
        signature_status = (
            "signed" if quotation.get("customer_signature", {}).get("signed_at") else "pending"
        )

        self._repo.update_by_id(
            quotation_id,
            {
                "email_delivery": {
                    "recipient_email": recipient_email,
                    "subject": subject,
                    "message": message,
                    "sent_at": now,
                    "pdf_file_name": pdf_file_name,
                },
                "portal_access_token": token,
                "portal_access_expires_at": expires_at,
                "signature_status": signature_status,
                "updated_by": actor,
            },
        )

        return {
            "id": quotation_id,
            "message": "견적서 메일 발송이 준비되었습니다",
            "recipient_email": recipient_email,
            "pdf_download_url": pdf_download_url,
            "portal_sign_url": portal_sign_url,
            "portal_access_token": token,
            "portal_access_expires_at": expires_at.isoformat(),
            "signature_status": signature_status,
        }

    def render_pdf(self, quotation_id: str) -> tuple[bytes, str]:
        quotation = self._get_quotation(quotation_id)

        lines = [
            f"Quotation {quotation_id}",
            f"Customer: {quotation.get('customer_name', '')}",
            f"Transaction Date: {self._format_date(quotation.get('transaction_date'))}",
            f"Valid Till: {self._format_date(quotation.get('valid_till'))}",
            "",
        ]
        for index, item in enumerate(quotation.get("items", []), start=1):
            amount = _decimal_amount(item.get("amount"))
            if amount == 0:
                amount = _decimal_amount(item.get("qty")) * _decimal_amount(item.get("rate"))
            lines.append(
                f"{index}. {item.get('item_name', item.get('item_code', 'ITEM'))} "
                f"x {_decimal_amount(item.get('qty'))} @ {_decimal_amount(item.get('rate'))} = {amount}"
            )
        lines.extend(
            [
                "",
                f"Total: {_decimal_amount(quotation.get('total'))}",
                f"Grand Total: {_decimal_amount(quotation.get('grand_total'))}",
                f"Signature Status: {quotation.get('signature_status', 'not_requested')}",
            ]
        )
        return _build_pdf_bytes(lines), f"{quotation_id}.pdf"

    def sign_from_portal(
        self,
        quotation_id: str,
        *,
        token: str,
        signer_name: str,
        signer_email: str,
        signature_text: str,
        signature_type: str,
    ) -> dict[str, Any]:
        quotation = self._get_submitted_quotation(quotation_id)

        stored_token = quotation.get("portal_access_token")
        if not stored_token or stored_token != token:
            raise_bad_request("유효하지 않은 포털 서명 토큰입니다")

        expires_at = _coerce_datetime(quotation.get("portal_access_expires_at"))
        now = datetime.now(tz=UTC)
        if expires_at and expires_at < now:
            raise_bad_request("포털 서명 토큰이 만료되었습니다")

        existing_signature = quotation.get("customer_signature") or {}
        if existing_signature.get("signed_at"):
            return {
                "id": quotation_id,
                "signature_status": "signed",
                "signed_at": existing_signature["signed_at"],
            }

        signature = {
            "signer_name": signer_name,
            "signer_email": signer_email,
            "signature_text": signature_text,
            "signature_type": signature_type,
            "signed_at": now,
        }
        self._repo.update_by_id(
            quotation_id,
            {
                "customer_signature": signature,
                "signature_status": "signed",
            },
        )

        return {
            "id": quotation_id,
            "message": "견적서에 전자서명이 완료되었습니다",
            "signature_status": "signed",
            "signed_at": now.isoformat(),
        }

    def _get_quotation(self, quotation_id: str) -> dict[str, Any]:
        quotation = self._repo.find_by_id(quotation_id)
        if not quotation:
            raise_not_found("견적서를 찾을 수 없습니다")
        return cast("dict[str, Any]", quotation)

    def _get_submitted_quotation(self, quotation_id: str) -> dict[str, Any]:
        quotation = self._get_quotation(quotation_id)
        if not _is_submitted_status(quotation.get("docstatus")):
            raise_bad_request("제출된 견적서만 고객에게 발송하거나 서명받을 수 있습니다")
        return quotation

    @staticmethod
    def _format_date(value: Any) -> str:
        dt = _coerce_datetime(value)
        if dt:
            return dt.date().isoformat()
        return str(value or "")
