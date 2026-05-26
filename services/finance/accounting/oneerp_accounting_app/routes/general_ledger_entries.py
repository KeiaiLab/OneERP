"""총계정원장 조회 라우터.

제출된 분개전표를 원장 라인으로 파생하여 기간/계정/전표 기준으로 조회한다.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_not_found
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.general_ledger_entry import GeneralLedgerLine, GeneralLedgerSummary

router = APIRouter(prefix="/api/v1/general-ledger-entries", tags=["총계정원장"])

_COLLECTION = "journal_entries"


def _get_repo(tenant_id: str) -> Repository:
    """총계정원장 원천인 분개전표 Repository를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _to_date(value: Any) -> date | None:
    """문자열/날짜를 date로 정규화한다."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _to_decimal(value: Any) -> Decimal:
    """숫자/문자열을 Decimal로 정규화한다."""
    if value in (None, ""):
        return Decimal(0)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _expand_lines(
    journal_entries: list[dict[str, Any]],
    *,
    account: str | None = None,
    voucher_no: str | None = None,
    voucher_type: str | None = None,
    cost_center: str | None = None,
) -> list[dict[str, Any]]:
    """제출된 분개전표를 총계정원장 라인으로 변환한다."""
    lines: list[dict[str, Any]] = []
    for journal_entry in journal_entries:
        if int(journal_entry.get("docstatus", 0)) != int(DocStatus.SUBMITTED):
            continue

        source_voucher_no = journal_entry.get("voucher_no") or journal_entry.get("_id", "")
        source_voucher_type = str(journal_entry.get("voucher_type", "")).strip()
        if voucher_no and source_voucher_no != voucher_no:
            continue
        if voucher_type and source_voucher_type != voucher_type:
            continue

        posting_date = _to_date(journal_entry.get("posting_date"))
        for index, item in enumerate(journal_entry.get("items", []), start=1):
            item_account = str(item.get("account", "")).strip()
            item_cost_center = str(item.get("cost_center") or "").strip()
            if account and item_account != account:
                continue
            if cost_center and item_cost_center != cost_center:
                continue

            line_idx = int(item.get("idx") or index)
            lines.append(
                {
                    "entry_id": f"{journal_entry.get('_id', '')}:{line_idx}",
                    "journal_entry_id": journal_entry.get("_id", ""),
                    "posting_date": posting_date,
                    "account": item_account,
                    "debit": _to_decimal(item.get("debit", 0)),
                    "credit": _to_decimal(item.get("credit", 0)),
                    "voucher_type": source_voucher_type,
                    "voucher_no": source_voucher_no,
                    "cost_center": item_cost_center,
                    "party_type": str(journal_entry.get("party_type", "")).strip(),
                    "party": str(journal_entry.get("party", "")).strip(),
                    "remarks": journal_entry.get("remark", ""),
                }
            )

    lines.sort(
        key=lambda line: (
            line["posting_date"] or date.min,
            line["journal_entry_id"],
            line["entry_id"],
        )
    )
    return lines


def _apply_running_balance(lines: list[dict[str, Any]], *, opening_balance: Decimal) -> None:
    """원장 라인에 누적 잔액을 계산해 주입한다."""
    running_balance = opening_balance
    for line in lines:
        running_balance += line["debit"] - line["credit"]
        line["running_balance"] = running_balance


def _serialize_lines(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """원장 라인을 JSON 직렬화 가능한 dict로 변환한다."""
    serialized: list[dict[str, Any]] = []
    for line in lines:
        payload = GeneralLedgerLine.model_validate(line).model_dump(mode="python")
        for field in ("debit", "credit", "running_balance"):
            payload[field] = float(payload[field])
        serialized.append(payload)
    return serialized


@router.get("", dependencies=[Depends(require_permission("general_ledger:read"))])
def 총계정원장_목록(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    *,
    account: Annotated[str | None, Query(description="계정과목 필터")] = None,
    posting_date_from: Annotated[date | None, Query(description="조회 시작일")] = None,
    posting_date_to: Annotated[date | None, Query(description="조회 종료일")] = None,
    voucher_no: Annotated[str | None, Query(description="원천 전표 번호 필터")] = None,
    voucher_type: Annotated[str | None, Query(description="원천 전표 유형 필터")] = None,
    cost_center: Annotated[str | None, Query(description="원가센터 필터")] = None,
) -> dict[str, Any]:
    """총계정원장을 계정/기간/전표 기준으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    journal_entries = list(repo.find_many(sort=[("posting_date", 1), ("created_at", 1)]))
    lines = _expand_lines(
        journal_entries,
        account=account,
        voucher_no=voucher_no,
        voucher_type=voucher_type,
        cost_center=cost_center,
    )

    opening_balance = Decimal(0)
    if posting_date_from is not None:
        before_period = [
            line
            for line in lines
            if line["posting_date"] is not None and line["posting_date"] < posting_date_from
        ]
        opening_balance = sum(
            (line["debit"] - line["credit"] for line in before_period), Decimal(0)
        )

    filtered_lines = lines
    if posting_date_from is not None:
        filtered_lines = [
            line
            for line in filtered_lines
            if line["posting_date"] is not None and line["posting_date"] >= posting_date_from
        ]
    if posting_date_to is not None:
        filtered_lines = [
            line
            for line in filtered_lines
            if line["posting_date"] is not None and line["posting_date"] <= posting_date_to
        ]

    total_debit = sum((line["debit"] for line in filtered_lines), Decimal(0))
    total_credit = sum((line["credit"] for line in filtered_lines), Decimal(0))

    _apply_running_balance(filtered_lines, opening_balance=opening_balance)

    skip = (page - 1) * page_size
    paged_lines = filtered_lines[skip : skip + page_size]
    summary = GeneralLedgerSummary(
        opening_balance=opening_balance,
        total_debit=total_debit,
        total_credit=total_credit,
        closing_balance=opening_balance + total_debit - total_credit,
    ).model_dump(mode="python")
    for field in ("opening_balance", "total_debit", "total_credit", "closing_balance"):
        summary[field] = float(summary[field])
    return {
        "data": _serialize_lines(paged_lines),
        "total": len(filtered_lines),
        "page": page,
        "page_size": page_size,
        "summary": summary,
    }


@router.get("/{entry_id}", dependencies=[Depends(require_permission("general_ledger:read"))])
def 총계정원장_조회(entry_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """총계정원장 라인 상세를 전표 라인 기준으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    journal_entries = list(repo.find_many(sort=[("posting_date", 1), ("created_at", 1)]))
    all_lines = _expand_lines(journal_entries)
    target = next((line for line in all_lines if line["entry_id"] == entry_id), None)
    if target is None:
        raise_not_found("총계정원장 항목을 찾을 수 없습니다")
    assert target is not None

    account_lines = [line for line in all_lines if line["account"] == target["account"]]
    _apply_running_balance(account_lines, opening_balance=Decimal(0))
    resolved = next((line for line in account_lines if line["entry_id"] == entry_id), None)
    if resolved is None:
        raise_not_found("총계정원장 항목을 찾을 수 없습니다")
    assert resolved is not None
    payload = GeneralLedgerLine.model_validate(resolved).model_dump(mode="python")
    for field in ("debit", "credit", "running_balance"):
        payload[field] = float(payload[field])
    return payload
