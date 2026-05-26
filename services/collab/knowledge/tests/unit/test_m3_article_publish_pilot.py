"""M3 collab/knowledge 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_knowledge_app.services.article_publish_pilot_service import (
    ArticlePublishPilotService,
    ArticlePublishSubmissionResult,
)


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = ArticlePublishPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "article_publish_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("article_publish_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "APR-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "publish_no": "APR-2026-0001",
            "article_id": "ART-A",
            "title": "신제품 출시 안내",
        }
    )
    result = svc.submit("APR-001")
    assert isinstance(result, ArticlePublishSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert repo.write_outbox.called


def test_차단_KNW_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "APR-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "publish_no": "APR-2026-0002",
            "article_id": "ART-B",
            "title": "보안 정책 업데이트",
        }
    )
    with pytest.raises(ValueError, match=ERR.KNW_001.value) as excinfo:
        svc.submit("APR-002")
    assert excinfo.value.args[0]["code"] == ERR.KNW_001.value
