"""M3 consolidation 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_finance_extra_app.consolidation.services.consol_entry_pilot_service import (
    ConsolEntryPilotService,
    ConsolEntrySubmissionResult,
)


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = ConsolEntryPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "consol_entry_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("consol_entry_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "CSL-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "entry_no": "CSL-2026-04",
            "period": "2026-04",
            "consol_type": "equity",
        }
    )
    result = svc.submit("CSL-001")
    assert isinstance(result, ConsolEntrySubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert result.consol_type == "equity"
    assert repo.write_outbox.called


def test_차단_CSL_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "CSL-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "entry_no": "CSL-2026-03",
            "period": "2026-03",
            "consol_type": "intercompany",
        }
    )
    with pytest.raises(ValueError, match=ERR.CSL_001.value) as excinfo:
        svc.submit("CSL-002")
    assert excinfo.value.args[0]["code"] == ERR.CSL_001.value
