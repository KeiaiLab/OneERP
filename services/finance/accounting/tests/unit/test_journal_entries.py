"""분개전표(Journal Entry) CRUD 엔드포인트 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from oneerp_accounting_app.main import app
from oneerp_core.document import DocStatus

client = TestClient(app)
client.headers.update(
    {
        "X-Tenant-Id": "test-tenant",
        "X-User-Sub": "test-user",
        "X-User-Roles": "admin",
        "X-User-Permissions": "*:*",
        "X-User-Tier": "super_admin",
    }
)


_BASE_URL = "/api/v1/journal-entries"


def test_분개전표_생성_정상(mock_collection: MagicMock) -> None:
    """POST /api/v1/journal-entries — 차대변 일치 시 201을 반환한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="JE-2026-00001")
    response = client.post(
        _BASE_URL,
        json={
            "posting_date": "2026-03-17",
            "items": [
                {"account": "ACC-2026-00001", "debit": 100000, "credit": 0, "idx": 1},
                {"account": "ACC-2026-00002", "debit": 0, "credit": 100000, "idx": 2},
            ],
            "remark": "테스트 분개",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["total_debit"] == 100000
    assert data["total_credit"] == 100000
    assert "_id" in data


def test_분개전표_생성_차대변_불일치_422(mock_collection: MagicMock) -> None:
    """EX-ACCT-001: 차대변 불일치 시 422 에러를 반환한다 (BR-ACCT-001)."""
    response = client.post(
        _BASE_URL,
        json={
            "posting_date": "2026-03-17",
            "items": [
                {"account": "ACC-2026-00001", "debit": 100000, "credit": 0, "idx": 1},
                {"account": "ACC-2026-00002", "debit": 0, "credit": 50000, "idx": 2},
            ],
        },
    )
    assert response.status_code == 422


def test_분개전표_생성_최소라인_미충족_422(mock_collection: MagicMock) -> None:
    """BR-ACCT-002: 라인 아이템이 2개 미만이면 422 에러를 반환한다."""
    response = client.post(
        _BASE_URL,
        json={
            "posting_date": "2026-03-17",
            "items": [
                {"account": "ACC-2026-00001", "debit": 100000, "credit": 0, "idx": 1},
            ],
        },
    )
    assert response.status_code == 422


def test_분개전표_생성_빈라인_422(mock_collection: MagicMock) -> None:
    """BR-ACCT-002: 빈 라인 아이템 배열이면 422 에러를 반환한다."""
    response = client.post(
        _BASE_URL,
        json={
            "posting_date": "2026-03-17",
            "items": [],
        },
    )
    assert response.status_code == 422


def test_분개전표_생성_마감기간_422(mock_collection: MagicMock) -> None:
    """EX-ACCT-003: 마감된 회계기간에 전표 입력 시 422 에러 (BR-ACCT-003)."""
    # accounting_periods 컬렉션에 마감된 기간 설정
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(
        return_value=iter(
            [
                {
                    "_id": "APD-001",
                    "start_date": "2026-01-01",
                    "end_date": "2026-01-31",
                    "status": "closed",
                    "tenant_id": "test-tenant",
                },
            ]
        )
    )
    mock_collection.find.return_value = mock_cursor

    response = client.post(
        _BASE_URL,
        json={
            "posting_date": "2026-01-15",
            "items": [
                {"account": "ACC-001", "debit": 100000, "credit": 0, "idx": 1},
                {"account": "ACC-002", "debit": 0, "credit": 100000, "idx": 2},
            ],
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"] == "ERR-ACCT-031"


def test_분개전표_수정_비Draft_상태_거부(mock_collection: MagicMock) -> None:
    """BR-ACCT-004: 제출된(SUBMITTED) 전표는 수정할 수 없다."""
    mock_collection.find_one.return_value = {
        "_id": "JE-2026-00001",
        "docstatus": DocStatus.SUBMITTED,
        "tenant_id": "test-tenant",
        "posting_date": "2026-03-17",
        "total_debit": 100000,
        "total_credit": 100000,
    }
    response = client.put(
        f"{_BASE_URL}/JE-2026-00001",
        json={"remark": "수정 시도"},
    )
    # check_draft_status는 400 Bad Request를 반환한다
    assert response.status_code == 400


def test_분개전표_수정_취소_상태_거부(mock_collection: MagicMock) -> None:
    """BR-ACCT-004: 취소된(CANCELLED) 전표도 수정할 수 없다."""
    mock_collection.find_one.return_value = {
        "_id": "JE-2026-00002",
        "docstatus": DocStatus.CANCELLED,
        "tenant_id": "test-tenant",
        "posting_date": "2026-03-17",
        "total_debit": 100000,
        "total_credit": 100000,
    }
    response = client.put(
        f"{_BASE_URL}/JE-2026-00002",
        json={"remark": "취소된 전표 수정 시도"},
    )
    assert response.status_code == 400


def test_분개전표_수정_Draft_상태_성공(mock_collection: MagicMock) -> None:
    """BR-ACCT-004: Draft 상태의 전표는 수정할 수 있다."""
    mock_collection.find_one.return_value = {
        "_id": "JE-2026-00003",
        "docstatus": DocStatus.DRAFT,
        "tenant_id": "test-tenant",
        "posting_date": "2026-03-17",
        "total_debit": 100000,
        "total_credit": 100000,
        "remark": "원본",
    }
    mock_collection.update_one.return_value = MagicMock(modified_count=1)
    # 마감 기간 검증용 — 마감 기간 없음
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(return_value=iter([]))
    mock_collection.find.return_value = mock_cursor

    response = client.put(
        f"{_BASE_URL}/JE-2026-00003",
        json={"remark": "수정된 적요"},
    )
    assert response.status_code == 200


def test_분개전표_목록_조회(mock_collection: MagicMock) -> None:
    """GET /api/v1/journal-entries — 분개전표 목록을 페이지네이션으로 조회한다."""
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.__iter__ = MagicMock(
        return_value=iter(
            [
                {
                    "_id": "JE-2026-00001",
                    "posting_date": "2026-03-17",
                    "total_debit": 100000,
                    "total_credit": 100000,
                    "tenant_id": "default",
                },
            ]
        )
    )
    mock_collection.find.return_value = mock_cursor
    mock_collection.count_documents.return_value = 1
    response = client.get(_BASE_URL)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert len(data["data"]) == 1


def test_분개전표_제출(mock_collection: MagicMock) -> None:
    """POST /api/v1/journal-entries/{doc_id}/submit — 초안 전표를 제출한다."""
    mock_collection.find_one.return_value = {
        "_id": "JE-2026-00001",
        "docstatus": DocStatus.DRAFT,
        "tenant_id": "default",
    }
    mock_collection.update_one.return_value = MagicMock(modified_count=1)
    response = client.post(f"{_BASE_URL}/JE-2026-00001/submit")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "JE-2026-00001"
    assert data["message"] == "분개전표가 제출되었습니다"


@patch("oneerp_accounting_app.routes.journal_entries.JournalAutoService")
def test_급여대장에서_분개전표_생성_정상(mock_service_cls: MagicMock) -> None:
    """POST /api/v1/journal-entries/from-payroll-entry — 급여 이벤트 payload를 분개로 변환한다."""
    service = MagicMock()
    service.create_payroll_journal_from_event.return_value = "JE-2026-00999"
    mock_service_cls.return_value = service

    response = client.post(
        f"{_BASE_URL}/from-payroll-entry",
        json={
            "payroll_entry_id": "PRLE-001",
            "tenant_id": "test-tenant",
            "employee_count": 5,
            "total_amount": 3500000,
            "posting_date": "2026-04-10",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": "JE-2026-00999",
        "payroll_entry_id": "PRLE-001",
        "message": "급여대장 기준 분개전표가 생성되었습니다",
    }
    service.create_payroll_journal_from_event.assert_called_once_with(
        {
            "doc_id": "PRLE-001",
            "employee_count": 5,
            "posting_date": "2026-04-10",
            "total_gross": 3500000,
            "total_net": 3500000,
            "total_employee_insurance": 0,
            "total_employer_insurance": 0,
            "total_income_tax": 0,
            "total_local_income_tax": 0,
        }
    )


@patch("oneerp_accounting_app.routes.journal_entries._get_repo")
def test_분개전표를_원장반영으로_표시한다(mock_repo: MagicMock) -> None:
    """POST /api/v1/journal-entries/{doc_id}/apply-to-ledger — 내부 원장 반영 상태를 기록한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "JE-2026-00011",
        "docstatus": DocStatus.SUBMITTED,
        "tenant_id": "test-tenant",
    }
    mock_repo.return_value = repo

    response = client.post(
        f"{_BASE_URL}/JE-2026-00011/apply-to-ledger",
        json={
            "journal_entry_id": "JE-2026-00011",
            "tenant_id": "test-tenant",
            "total_debit": "100000",
            "total_credit": "100000",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == "JE-2026-00011"
    update_args = repo.update_by_id.call_args.args
    assert update_args[0] == "JE-2026-00011"
    assert update_args[1]["ledger_applied"] is True
    assert update_args[1]["ledger_total_debit"] == "100000"
    assert update_args[1]["ledger_total_credit"] == "100000"


def test_분개전표_취소(mock_collection: MagicMock) -> None:
    """POST /api/v1/journal-entries/{doc_id}/cancel — 제출된 전표를 취소한다."""
    mock_collection.find_one.return_value = {
        "_id": "JE-2026-00001",
        "docstatus": DocStatus.SUBMITTED,
        "tenant_id": "default",
    }
    mock_collection.update_one.return_value = MagicMock(modified_count=1)
    response = client.post(f"{_BASE_URL}/JE-2026-00001/cancel")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "JE-2026-00001"
    assert data["message"] == "분개전표가 취소되었습니다"


def test_분개전표_삭제_Draft_상태_성공(mock_collection: MagicMock) -> None:
    """Draft 상태 분개전표는 삭제할 수 있다."""
    mock_collection.find_one.return_value = {
        "_id": "JE-2026-00003",
        "docstatus": DocStatus.DRAFT,
        "tenant_id": "default",
    }
    mock_collection.delete_one.return_value = MagicMock(deleted_count=1)

    response = client.delete(f"{_BASE_URL}/JE-2026-00003")

    assert response.status_code == 204


def test_분개전표_삭제_제출상태_거부(mock_collection: MagicMock) -> None:
    """제출된 분개전표는 삭제할 수 없다."""
    mock_collection.find_one.return_value = {
        "_id": "JE-2026-00004",
        "docstatus": DocStatus.SUBMITTED,
        "tenant_id": "default",
    }

    response = client.delete(f"{_BASE_URL}/JE-2026-00004")

    assert response.status_code == 400


def test_분개전표_승인요청_정상(mock_collection: MagicMock) -> None:
    """초안 전표는 승인 요청으로 pending 상태가 되어야 한다."""
    mock_collection.find_one.return_value = {
        "_id": "JE-2026-00005",
        "docstatus": DocStatus.DRAFT,
        "tenant_id": "test-tenant",
        "posting_date": "2026-03-20",
        "approval_status": "not_requested",
    }
    mock_collection.update_one.return_value = MagicMock(modified_count=1)

    response = client.post(
        f"{_BASE_URL}/JE-2026-00005/request-approval",
        json={"approver": "finance-lead", "comment": "월말 조정 검토 요청"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["approval_status"] == "pending"
    assert body["required_approver"] == "finance-lead"


def test_분개전표_승인_지정결재자만_가능(
    mock_collection: MagicMock,
    test_client: TestClient,
) -> None:
    """지정된 결재자가 아니면 승인할 수 없다."""
    mock_collection.find_one.return_value = {
        "_id": "JE-2026-00006",
        "docstatus": DocStatus.DRAFT,
        "tenant_id": "test-tenant",
        "posting_date": "2026-03-20",
        "approval_status": "pending",
        "approval_required": True,
        "required_approver": "finance-lead",
    }

    test_client.headers["X-User-Sub"] = "another-user"
    response = test_client.post(f"{_BASE_URL}/JE-2026-00006/approve")

    assert response.status_code == 422


def test_분개전표_승인시_제출된다(
    mock_collection: MagicMock,
    test_client: TestClient,
) -> None:
    """지정 결재자가 승인하면 전표가 제출 상태가 된다."""
    mock_collection.find_one.return_value = {
        "_id": "JE-2026-00006",
        "docstatus": DocStatus.DRAFT,
        "tenant_id": "test-tenant",
        "posting_date": "2026-03-20",
        "approval_status": "pending",
        "approval_required": True,
        "required_approver": "finance-lead",
        "voucher_type": "journal_entry",
        "total_debit": 500000,
        "total_credit": 500000,
    }
    mock_collection.update_one.return_value = MagicMock(modified_count=1)
    test_client.headers["X-User-Sub"] = "finance-lead"

    response = test_client.post(f"{_BASE_URL}/JE-2026-00006/approve")

    assert response.status_code == 200
    assert response.json()["approval_status"] == "approved"


def test_분개전표_반려_사유를_기록한다(
    mock_collection: MagicMock,
    test_client: TestClient,
) -> None:
    """결재자는 대기 중 전표를 반려하고 사유를 남길 수 있어야 한다."""
    mock_collection.find_one.return_value = {
        "_id": "JE-2026-00007",
        "docstatus": DocStatus.DRAFT,
        "tenant_id": "test-tenant",
        "posting_date": "2026-03-20",
        "approval_status": "pending",
        "approval_required": True,
        "required_approver": "finance-lead",
    }
    mock_collection.update_one.return_value = MagicMock(modified_count=1)

    test_client.headers["X-User-Sub"] = "finance-lead"
    response = test_client.post(
        f"{_BASE_URL}/JE-2026-00007/reject",
        json={"reason": "증빙 첨부 필요"},
    )

    assert response.status_code == 200
    assert response.json()["approval_status"] == "rejected"


def test_분개전표_템플릿_생성(mock_collection: MagicMock) -> None:
    """반복 전표 템플릿을 저장할 수 있어야 한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="JETPL-2026-00001")

    response = client.post(
        f"{_BASE_URL}/templates",
        json={
            "template_name": "월말 선급비용 템플릿",
            "voucher_type": "recurring_adjustment",
            "recurrence_unit": "monthly",
            "interval": 1,
            "next_posting_date": "2026-04-30",
            "items": [
                {"account": "선급비용", "debit": 500000, "credit": 0, "idx": 1},
                {"account": "보험료", "debit": 0, "credit": 500000, "idx": 2},
            ],
            "remark": "월말 선급비용 조정",
            "default_approver": "finance-lead",
        },
    )

    assert response.status_code == 201
    assert response.json()["template_name"] == "월말 선급비용 템플릿"


def test_분개전표_템플릿으로_초안생성(mock_collection: MagicMock) -> None:
    """반복 전표 템플릿으로 다음 회차 초안 전표를 생성해야 한다."""
    mock_collection.find_one.return_value = {
        "_id": "JETPL-2026-00001",
        "tenant_id": "test-tenant",
        "template_name": "월말 선급비용 템플릿",
        "voucher_type": "recurring_adjustment",
        "recurrence_unit": "monthly",
        "interval": 1,
        "next_posting_date": "2026-04-30",
        "items": [
            {"account": "선급비용", "debit": 500000, "credit": 0, "idx": 1},
            {"account": "보험료", "debit": 0, "credit": 500000, "idx": 2},
        ],
        "remark": "월말 선급비용 조정",
        "default_approver": "finance-lead",
    }
    mock_collection.insert_one.return_value = MagicMock(inserted_id="JE-2026-00008")
    mock_collection.update_one.return_value = MagicMock(modified_count=1)

    response = client.post(
        f"{_BASE_URL}/templates/JETPL-2026-00001/instantiate",
        json={"posting_date": "2026-04-30"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["template_id"] == "JETPL-2026-00001"
    assert body["required_approver"] == "finance-lead"
