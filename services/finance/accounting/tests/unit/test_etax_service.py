"""전자세금계산서 국세청 API 연동 서비스 테스트."""

from __future__ import annotations

import asyncio
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from oneerp_accounting_app.services.etax_service import ETaxService
from oneerp_accounting_app.services.nts_api_client import MockNTSApiClient, create_nts_client
from oneerp_core.errors import OneERPError

_today_fn = date.today

# ---------------------------------------------------------------------------
# MockNTSApiClient 테스트
# ---------------------------------------------------------------------------


def test_mock_클라이언트_submit_confirmation_no_반환() -> None:
    """MockNTSApiClient.submit_invoice가 confirmation_no를 포함한 응답을 반환한다."""
    client = MockNTSApiClient()
    result = asyncio.run(client.submit_invoice({"doc_id": "ETAX-001"}))
    assert result["status"] == "accepted"
    assert result["confirmation_no"].startswith("NTS-")
    assert result["message"] == "전송 완료"


def test_mock_클라이언트_check_status_confirmed_반환() -> None:
    """MockNTSApiClient.check_status가 confirmed 상태를 반환한다."""
    client = MockNTSApiClient()
    result = asyncio.run(client.check_status("NTS-12345678"))
    assert result["status"] == "confirmed"
    assert result["confirmation_no"] == "NTS-12345678"


def test_mock_클라이언트_cancel_cancelled_반환() -> None:
    """MockNTSApiClient.cancel_invoice가 cancelled 상태를 반환한다."""
    client = MockNTSApiClient()
    result = asyncio.run(client.cancel_invoice("NTS-12345678", "테스트 취소"))
    assert result["status"] == "cancelled"
    assert result["confirmation_no"] == "NTS-12345678"


# ---------------------------------------------------------------------------
# create_nts_client 팩토리 테스트
# ---------------------------------------------------------------------------


def test_create_nts_client_환경변수_미설정_시_mock_반환() -> None:
    """ONEERP_NTS_API_URL 미설정 시 MockNTSApiClient를 반환한다."""
    with patch.dict("os.environ", {}, clear=True):
        client = create_nts_client()
        assert isinstance(client, MockNTSApiClient)


def test_create_nts_client_환경변수_설정_시에도_mock_반환() -> None:
    """ONEERP_NTS_API_URL 설정되어도 Phase 2에서는 Mock을 반환한다."""
    with patch.dict("os.environ", {"ONEERP_NTS_API_URL": "https://nts.example.com"}):
        client = create_nts_client()
        # Phase 2에서는 아직 실제 클라이언트가 없으므로 Mock 반환
        assert isinstance(client, MockNTSApiClient)


# ---------------------------------------------------------------------------
# ETaxService 테스트
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_nts_client() -> AsyncMock:
    """Mock NTS API 클라이언트를 반환한다."""
    client = AsyncMock()
    client.submit_invoice.return_value = {
        "status": "accepted",
        "confirmation_no": "NTS-TESTTEST",
        "message": "전송 완료",
    }
    client.check_status.return_value = {
        "status": "confirmed",
        "confirmation_no": "NTS-TESTTEST",
    }
    client.cancel_invoice.return_value = {
        "status": "cancelled",
        "confirmation_no": "NTS-TESTTEST",
    }
    return client


@pytest.fixture
def mock_repo() -> MagicMock:
    """Mock Repository를 반환한다."""
    return MagicMock()


@pytest.fixture
def etax_service(mock_nts_client: AsyncMock, mock_repo: MagicMock) -> ETaxService:
    """ETaxService 인스턴스를 반환한다."""
    with patch("oneerp_accounting_app.services.etax_service.Repository") as repo_cls:
        repo_cls.return_value = mock_repo
        return ETaxService(nts_client=mock_nts_client, tenant_id="test-tenant")


@pytest.fixture
def sample_invoice_doc() -> dict:
    """샘플 전자세금계산서 문서를 반환한다."""
    return {
        "_id": "ETAX-2026-00001",
        "tenant_id": "test-tenant",
        "invoice_ref": "SINV-001",
        # 테스트 시점에 항상 "기한 이내" 상태가 되도록 오늘 발급으로 설정
        # (BR-KTAX-017 취소기한 = 발급월 익월 10일 > 오늘)
        "issue_date": _today_fn().isoformat(),
        "supplier_or_customer": "테스트 고객",
        "supply_amount": 100000.0,
        "tax_amount": 10000.0,
        "transmission_status": "pending",
        "issue_type": "정발행",
        "receipt_type": "청구",
        "nts_confirmation_no": None,
    }


def test_submit_to_nts_전송_성공(
    etax_service: ETaxService,
    mock_repo: MagicMock,
    mock_nts_client: AsyncMock,
    sample_invoice_doc: dict,
) -> None:
    """submit_to_nts가 정상 실행 시 transmission_status를 sent로 업데이트한다."""
    mock_repo.find_by_id.return_value = sample_invoice_doc

    result = asyncio.run(etax_service.submit_to_nts("ETAX-2026-00001"))

    assert result["transmission_status"] == "sent"
    assert result["nts_confirmation_no"] == "NTS-TESTTEST"
    assert result["doc_id"] == "ETAX-2026-00001"

    # nts_client.submit_invoice가 호출되었는지 확인
    mock_nts_client.submit_invoice.assert_called_once()

    # DB 업데이트가 호출되었는지 확인
    mock_repo.update_by_id.assert_called_once()
    update_args = mock_repo.update_by_id.call_args
    assert update_args[0][0] == "ETAX-2026-00001"
    assert update_args[0][1]["transmission_status"] == "sent"
    assert update_args[0][1]["nts_confirmation_no"] == "NTS-TESTTEST"


def test_submit_to_nts_이미_전송된_문서_에러(
    etax_service: ETaxService,
    mock_repo: MagicMock,
    sample_invoice_doc: dict,
) -> None:
    """이미 전송된 문서를 다시 전송하면 OneERPError가 발생한다."""
    sample_invoice_doc["transmission_status"] = "sent"
    mock_repo.find_by_id.return_value = sample_invoice_doc

    with pytest.raises(OneERPError, match="ERR-KTAX-030"):
        asyncio.run(etax_service.submit_to_nts("ETAX-2026-00001"))


def test_check_nts_status_정상_조회(
    etax_service: ETaxService,
    mock_repo: MagicMock,
    mock_nts_client: AsyncMock,
    sample_invoice_doc: dict,
) -> None:
    """check_nts_status가 국세청 상태를 정상 조회한다."""
    sample_invoice_doc["nts_confirmation_no"] = "NTS-TESTTEST"
    mock_repo.find_by_id.return_value = sample_invoice_doc

    result = asyncio.run(etax_service.check_nts_status("ETAX-2026-00001"))

    assert result["nts_status"] == "confirmed"
    assert result["confirmation_no"] == "NTS-TESTTEST"
    mock_nts_client.check_status.assert_called_once_with("NTS-TESTTEST")


def test_check_nts_status_승인번호_없음_에러(
    etax_service: ETaxService,
    mock_repo: MagicMock,
    sample_invoice_doc: dict,
) -> None:
    """nts_confirmation_no가 없으면 OneERPError가 발생한다."""
    sample_invoice_doc["nts_confirmation_no"] = None
    mock_repo.find_by_id.return_value = sample_invoice_doc

    with pytest.raises(OneERPError, match="ERR-KTAX-030"):
        asyncio.run(etax_service.check_nts_status("ETAX-2026-00001"))


def test_cancel_nts_취소_성공(
    etax_service: ETaxService,
    mock_repo: MagicMock,
    mock_nts_client: AsyncMock,
    sample_invoice_doc: dict,
) -> None:
    """cancel_nts가 정상 실행 시 cancelled 상태를 반환한다."""
    sample_invoice_doc["nts_confirmation_no"] = "NTS-TESTTEST"
    mock_repo.find_by_id.return_value = sample_invoice_doc

    result = asyncio.run(etax_service.cancel_nts("ETAX-2026-00001", "테스트 취소 사유"))

    assert result["nts_status"] == "cancelled"
    assert result["confirmation_no"] == "NTS-TESTTEST"
    mock_nts_client.cancel_invoice.assert_called_once_with("NTS-TESTTEST", "테스트 취소 사유")

    # DB 업데이트 확인
    update_args = mock_repo.update_by_id.call_args
    assert update_args[0][1]["transmission_status"] == "cancelled"


def test_cancel_nts_승인번호_없음_에러(
    etax_service: ETaxService,
    mock_repo: MagicMock,
    sample_invoice_doc: dict,
) -> None:
    """nts_confirmation_no가 없으면 cancel도 OneERPError가 발생한다."""
    sample_invoice_doc["nts_confirmation_no"] = None
    mock_repo.find_by_id.return_value = sample_invoice_doc

    with pytest.raises(OneERPError, match="ERR-KTAX-030"):
        asyncio.run(etax_service.cancel_nts("ETAX-2026-00001", "취소 사유"))


def test_미존재_문서_에러(
    etax_service: ETaxService,
    mock_repo: MagicMock,
) -> None:
    """존재하지 않는 문서 ID로 호출하면 OneERPError가 발생한다."""
    mock_repo.find_by_id.return_value = None

    with pytest.raises(OneERPError, match="not_found"):
        asyncio.run(etax_service.submit_to_nts("NOT-EXIST"))

    with pytest.raises(OneERPError, match="not_found"):
        asyncio.run(etax_service.check_nts_status("NOT-EXIST"))

    with pytest.raises(OneERPError, match="not_found"):
        asyncio.run(etax_service.cancel_nts("NOT-EXIST", "사유"))


# ---------------------------------------------------------------------------
# BR-KTAX-017: 취소 기한 검증 테스트
# ---------------------------------------------------------------------------


def test_cancel_nts_취소기한_초과_에러(
    etax_service: ETaxService,
    mock_repo: MagicMock,
    sample_invoice_doc: dict,
) -> None:
    """BR-KTAX-017: 발급일 익월 10일 이후 취소 시 ERR-KTAX-031 에러."""
    from datetime import date
    from unittest.mock import patch as _patch

    sample_invoice_doc["nts_confirmation_no"] = "NTS-TESTTEST"
    sample_invoice_doc["issue_date"] = "2026-01-15"
    mock_repo.find_by_id.return_value = sample_invoice_doc

    # 오늘을 2026-02-15 (발급일 1/15 → 기한 2/10 초과)로 고정
    with _patch(
        "oneerp_accounting_app.services.etax_service.datetime",
    ) as mock_dt:
        mock_dt.now.return_value = MagicMock()
        mock_dt.now.return_value.date.return_value = date(2026, 2, 15)
        mock_dt.side_effect = lambda *a, **k: MagicMock()

        with pytest.raises(OneERPError, match="ERR-KTAX-031"):
            asyncio.run(etax_service.cancel_nts("ETAX-2026-00001", "취소"))


def test_cancel_nts_취소기한_이내_성공(
    etax_service: ETaxService,
    mock_repo: MagicMock,
    mock_nts_client: AsyncMock,
    sample_invoice_doc: dict,
) -> None:
    """BR-KTAX-017: 발급일 익월 10일 이전이면 정상 취소."""
    sample_invoice_doc["nts_confirmation_no"] = "NTS-TESTTEST"
    # fixture 의 issue_date 가 이미 오늘(기한 이내) 이라 override 불필요
    mock_repo.find_by_id.return_value = sample_invoice_doc

    # datetime.now()가 기한 이전을 반환하도록 설정됨 (기본)
    result = asyncio.run(etax_service.cancel_nts("ETAX-2026-00001", "취소"))
    assert result["nts_status"] == "cancelled"


def test_cancel_deadline_12월_연도넘김() -> None:
    """BR-KTAX-017: 12월 발급 시 기한은 다음해 1월 10일."""
    from datetime import date

    from oneerp_accounting_app.services.etax_service import _cancel_deadline

    deadline = _cancel_deadline(date(2026, 12, 25))
    assert deadline == date(2027, 1, 10)


def test_cancel_deadline_일반월() -> None:
    """BR-KTAX-017: 일반월 발급 시 기한은 익월 10일."""
    from datetime import date

    from oneerp_accounting_app.services.etax_service import _cancel_deadline

    deadline = _cancel_deadline(date(2026, 3, 1))
    assert deadline == date(2026, 4, 10)


# ---------------------------------------------------------------------------
# BR-KTAX-013: 사업자등록번호 검증 테스트
# ---------------------------------------------------------------------------


def test_사업자등록번호_정상_하이픈포함() -> None:
    """BR-KTAX-013: 유효한 사업자등록번호(하이픈 포함) 검증 통과."""
    from oneerp_accounting_app.services.etax_service import validate_brn

    # 국세청 공식 사업자등록번호 예시: 120-81-47521
    assert validate_brn("120-81-47521") is True


def test_사업자등록번호_정상_하이픈없음() -> None:
    """BR-KTAX-013: 하이픈 없는 10자리도 검증 통과."""
    from oneerp_accounting_app.services.etax_service import validate_brn

    assert validate_brn("1208147521") is True


def test_사업자등록번호_길이_오류() -> None:
    """BR-KTAX-013: 10자리가 아닌 번호는 실패."""
    from oneerp_accounting_app.services.etax_service import validate_brn

    assert validate_brn("123-45-6789") is False  # 9자리
    assert validate_brn("123-45-678901") is False  # 11자리


def test_사업자등록번호_비숫자_오류() -> None:
    """BR-KTAX-013: 숫자가 아닌 문자 포함 시 실패."""
    from oneerp_accounting_app.services.etax_service import validate_brn

    assert validate_brn("12A-81-47521") is False


def test_사업자등록번호_체크디짓_오류() -> None:
    """BR-KTAX-013: 체크디짓 불일치 시 실패."""
    from oneerp_accounting_app.services.etax_service import validate_brn

    assert validate_brn("120-81-47522") is False  # 마지막 자리 변조


# ---------------------------------------------------------------------------
# BR-KTAX-004: 부가세 신고 기간 분류 테스트
# ---------------------------------------------------------------------------


def test_부가세_기간분류_1기예정() -> None:
    """BR-KTAX-004: 1~3월 = 1기 예정."""
    from datetime import date

    from oneerp_accounting_app.services.vat_service import classify_vat_period

    assert classify_vat_period(date(2026, 1, 1)) == "2026년 1기 예정"
    assert classify_vat_period(date(2026, 3, 31)) == "2026년 1기 예정"


def test_부가세_기간분류_1기확정() -> None:
    """BR-KTAX-004: 4~6월 = 1기 확정."""
    from datetime import date

    from oneerp_accounting_app.services.vat_service import classify_vat_period

    assert classify_vat_period(date(2026, 4, 1)) == "2026년 1기 확정"


def test_부가세_기간분류_2기예정() -> None:
    """BR-KTAX-004: 7~9월 = 2기 예정."""
    from datetime import date

    from oneerp_accounting_app.services.vat_service import classify_vat_period

    assert classify_vat_period(date(2026, 7, 15)) == "2026년 2기 예정"


def test_부가세_기간분류_2기확정() -> None:
    """BR-KTAX-004: 10~12월 = 2기 확정."""
    from datetime import date

    from oneerp_accounting_app.services.vat_service import classify_vat_period

    assert classify_vat_period(date(2026, 12, 31)) == "2026년 2기 확정"


def test_submit_to_nts_xml_payload_생성_확인(
    etax_service: ETaxService,
    mock_repo: MagicMock,
    mock_nts_client: AsyncMock,
    sample_invoice_doc: dict,
) -> None:
    """submit_to_nts가 XML 페이로드를 생성하여 DB에 저장한다."""
    mock_repo.find_by_id.return_value = sample_invoice_doc

    asyncio.run(etax_service.submit_to_nts("ETAX-2026-00001"))

    update_args = mock_repo.update_by_id.call_args
    xml_payload = update_args[0][1]["xml_payload"]
    assert "TaxInvoice" in xml_payload
    assert "ETAX-2026-00001" in xml_payload
    assert "테스트 고객" in xml_payload
