"""M3 collab/board 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_board_app.services.board_post_pilot_service import (
    BoardPostPilotService,
    BoardPostSubmissionResult,
)
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = BoardPostPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "board_post_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("board_post_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "BP-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "post_no": "BP-2026-0001",
            "board_id": "BRD-NOTICE",
            "title": "사내 공지",
        }
    )
    result = svc.submit("BP-001")
    assert isinstance(result, BoardPostSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert repo.write_outbox.called


def test_차단_BRD_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "BP-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "post_no": "BP-2026-0002",
            "board_id": "BRD-NEWS",
            "title": "이전 공지",
        }
    )
    with pytest.raises(ValueError, match=ERR.BRD_001.value) as excinfo:
        svc.submit("BP-002")
    assert excinfo.value.args[0]["code"] == ERR.BRD_001.value
