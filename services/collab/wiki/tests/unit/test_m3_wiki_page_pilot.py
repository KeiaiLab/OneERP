"""M3 collab/wiki 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_wiki_app.services.wiki_page_pilot_service import (
    WikiPagePilotService,
    WikiPageSubmissionResult,
)


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = WikiPagePilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "wiki_page_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("wiki_page_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "WP-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "page_no": "WP-2026-0001",
            "space": "engineering",
            "title": "코딩 컨벤션",
        }
    )
    result = svc.submit("WP-001")
    assert isinstance(result, WikiPageSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert repo.write_outbox.called


def test_차단_WIK_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "WP-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "page_no": "WP-2026-0002",
            "space": "ops",
            "title": "장애 대응 가이드",
        }
    )
    with pytest.raises(ValueError, match=ERR.WIK_001.value) as excinfo:
        svc.submit("WP-002")
    assert excinfo.value.args[0]["code"] == ERR.WIK_001.value
