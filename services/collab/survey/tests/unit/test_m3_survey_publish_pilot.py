"""M3 collab/survey 파일럿 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.document import DocStatus
from oneerp_core.error_catalog import ERR
from oneerp_core.uow import UnitOfWork
from oneerp_survey_app.services.survey_publish_pilot_service import (
    SurveyPublishPilotService,
    SurveyPublishSubmissionResult,
)


def _make_svc(doc_raw):
    uow = UnitOfWork(tenant_id="t1")
    svc = SurveyPublishPilotService(tenant_id="t1", uow=uow)
    repo = MagicMock()
    repo.find_by_id.return_value = doc_raw
    repo.collection_name = "survey_publish_pilot"
    repo.write_outbox = MagicMock()
    svc.register_repo("survey_publish_pilot", repo)
    return svc, repo


def test_제출_정상() -> None:
    svc, repo = _make_svc(
        {
            "_id": "SV-001",
            "tenant_id": "t1",
            "docstatus": DocStatus.DRAFT,
            "survey_no": "SV-2026-Q2",
            "title": "직원 만족도 조사",
            "target_audience": "all_employees",
        }
    )
    result = svc.submit("SV-001")
    assert isinstance(result, SurveyPublishSubmissionResult)
    assert result.docstatus == DocStatus.SUBMITTED
    assert repo.write_outbox.called


def test_차단_SUR_001() -> None:
    svc, _ = _make_svc(
        {
            "_id": "SV-002",
            "tenant_id": "t1",
            "docstatus": DocStatus.SUBMITTED,
            "survey_no": "SV-2026-Q1",
            "title": "고객 NPS",
            "target_audience": "customers",
        }
    )
    with pytest.raises(ValueError, match=ERR.SUR_001.value) as excinfo:
        svc.submit("SV-002")
    assert excinfo.value.args[0]["code"] == ERR.SUR_001.value
