"""견적→판매주문 전환 서비스 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError
from oneerp_selling_app.services.quotation_conversion_service import QuotationConversionService


@pytest.fixture
def mock_repos():
    """quotations 및 sales_orders 컬렉션 mock을 설정한다."""
    with (
        patch("oneerp_core.repository.get_client") as mock_client,
        patch("oneerp_core.naming.get_client") as mock_naming_client,
    ):
        mock_col = MagicMock()
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_client.return_value.__getitem__ = MagicMock(return_value=mock_db)

        # insert_one / update_one 반환값 설정
        mock_insert_result = MagicMock()
        mock_insert_result.inserted_id = "mock-id"
        mock_col.insert_one.return_value = mock_insert_result

        mock_update_result = MagicMock()
        mock_update_result.modified_count = 1
        mock_col.update_one.return_value = mock_update_result

        mock_naming_db = MagicMock()
        mock_naming_counters = MagicMock()
        mock_naming_db.__getitem__ = MagicMock(return_value=mock_naming_counters)
        mock_naming_client.return_value.__getitem__ = MagicMock(return_value=mock_naming_db)
        mock_naming_counters.find_one_and_update.return_value = {"seq": 1}

        yield mock_col


def test_전체_전환_성공(mock_repos):
    """견적서 전체 아이템을 판매주문으로 변환하고 원본에 converted_to를 기록한다."""
    quotation = {
        "_id": "QTN-0001",
        "customer_id": "CUST-001",
        "docstatus": "submitted",
        "items": [
            {"item_code": "ITEM-A", "qty": 10, "rate": 1000},
            {"item_code": "ITEM-B", "qty": 5, "rate": 2000},
        ],
    }
    mock_repos.find_one.return_value = quotation
    mock_repos.find_one_and_update.return_value = quotation

    svc = QuotationConversionService(tenant_id="T001")
    result = svc.convert_to_sales_order("QTN-0001")

    assert result["source_quotation"] == "QTN-0001"
    assert len(result["items"]) == 2
    assert result["so_id"].startswith("SO-")
    # converted_to 업데이트 호출 확인
    mock_repos.update_one.assert_called()


def test_부분_전환(mock_repos):
    """item_indices 지정 시 해당 인덱스의 아이템만 판매주문에 포함된다."""
    quotation = {
        "_id": "QTN-0002",
        "customer_id": "CUST-002",
        "docstatus": "submitted",
        "items": [
            {"item_code": "ITEM-A", "qty": 10, "rate": 1000},
            {"item_code": "ITEM-B", "qty": 5, "rate": 2000},
            {"item_code": "ITEM-C", "qty": 3, "rate": 3000},
        ],
    }
    mock_repos.find_one.return_value = quotation

    svc = QuotationConversionService(tenant_id="T001")
    result = svc.convert_to_sales_order("QTN-0002", item_indices=[0, 2])

    assert len(result["items"]) == 2
    assert result["items"][0]["item_code"] == "ITEM-A"
    assert result["items"][1]["item_code"] == "ITEM-C"


def test_이미_전환된_견적_재전환_실패(mock_repos):
    """converted_to가 이미 존재하는 견적서는 ValueError를 발생시킨다."""
    quotation = {
        "_id": "QTN-0003",
        "docstatus": "submitted",
        "converted_to": "SO-0001",
        "items": [],
    }
    mock_repos.find_one.return_value = quotation

    svc = QuotationConversionService(tenant_id="T001")
    with pytest.raises(OneERPError, match="ERR-SELL-025"):
        svc.convert_to_sales_order("QTN-0003")


def test_취소된_견적_전환_실패(mock_repos):
    """BR-SELL-001: CANCELLED 상태인 견적서는 전환할 수 없다."""
    quotation = {
        "_id": "QTN-0004",
        "docstatus": "cancelled",
        "items": [],
    }
    mock_repos.find_one.return_value = quotation

    svc = QuotationConversionService(tenant_id="T001")
    with pytest.raises(OneERPError, match="ERR-SELL-030"):
        svc.convert_to_sales_order("QTN-0004")


def test_유효기한_경과_견적_전환_경고(mock_repos, caplog):
    """BR-SELL-017: 유효기한 경과 시 경고만 남기고 전환은 성공한다."""
    import logging

    quotation = {
        "_id": "QTN-0005",
        "customer_id": "CUST-005",
        "docstatus": "submitted",
        "valid_till": "2025-01-01",  # 과거 날짜
        "items": [
            {"item_code": "ITEM-A", "qty": 5, "rate": 1000},
        ],
    }
    mock_repos.find_one.return_value = quotation

    svc = QuotationConversionService(tenant_id="T001")
    with caplog.at_level(logging.WARNING):
        result = svc.convert_to_sales_order("QTN-0005")

    assert result["so_id"].startswith("SO-")
    assert "유효기한 경과" in caplog.text


def test_미존재_견적_에러(mock_repos):
    """BR-SELL-001: 존재하지 않는 견적서 ID로 전환 시 not_found 에러."""
    mock_repos.find_one.return_value = None

    svc = QuotationConversionService(tenant_id="T001")
    with pytest.raises(OneERPError, match="not_found"):
        svc.convert_to_sales_order("QTN-NONEXIST")


def test_Draft_견적_전환_실패(mock_repos):
    """BR-SELL-001: Draft(미제출) 견적서는 전환할 수 없다."""
    quotation = {
        "_id": "QTN-0006",
        "docstatus": "draft",
        "items": [{"item_code": "ITEM-A", "qty": 1, "rate": 100}],
    }
    mock_repos.find_one.return_value = quotation

    svc = QuotationConversionService(tenant_id="T001")
    with pytest.raises(OneERPError, match="ERR-SELL-030"):
        svc.convert_to_sales_order("QTN-0006")


# ---------- BR-SELL-002: 유효하지 않은 아이템 인덱스 검증 ----------


def _submitted_quotation_with_items(n: int = 3) -> dict:
    """n개 아이템을 가진 제출 상태 견적서 fixture 데이터를 생성한다."""
    return {
        "_id": "QTN-IDX",
        "customer_id": "CUST-IDX",
        "docstatus": "submitted",
        "items": [{"item_code": f"ITEM-{i}", "qty": 1, "rate": 100} for i in range(n)],
    }


def test_범위_초과_인덱스_에러(mock_repos):
    """BR-SELL-002: item_indices에 범위 초과 인덱스가 포함되면 ERR-SELL-032 에러."""
    quotation = _submitted_quotation_with_items(3)
    mock_repos.find_one.return_value = quotation

    svc = QuotationConversionService(tenant_id="T001")
    with pytest.raises(OneERPError, match="ERR-SELL-032"):
        svc.convert_to_sales_order("QTN-IDX", item_indices=[0, 5])


def test_음수_인덱스_에러(mock_repos):
    """BR-SELL-002: 음수 인덱스도 유효하지 않은 것으로 거부한다."""
    quotation = _submitted_quotation_with_items(3)
    mock_repos.find_one.return_value = quotation

    svc = QuotationConversionService(tenant_id="T001")
    with pytest.raises(OneERPError, match="ERR-SELL-032"):
        svc.convert_to_sales_order("QTN-IDX", item_indices=[-1])


def test_경계값_마지막_인덱스_성공(mock_repos):
    """BR-SELL-002: 마지막 유효 인덱스(len-1)는 정상 처리된다."""
    quotation = _submitted_quotation_with_items(3)
    mock_repos.find_one.return_value = quotation

    svc = QuotationConversionService(tenant_id="T001")
    result = svc.convert_to_sales_order("QTN-IDX", item_indices=[2])

    assert len(result["items"]) == 1
    assert result["items"][0]["item_code"] == "ITEM-2"


def test_경계값_len과_같은_인덱스_에러(mock_repos):
    """BR-SELL-002: len(items)과 같은 인덱스는 범위 밖이므로 에러."""
    quotation = _submitted_quotation_with_items(3)
    mock_repos.find_one.return_value = quotation

    svc = QuotationConversionService(tenant_id="T001")
    with pytest.raises(OneERPError, match="ERR-SELL-032"):
        svc.convert_to_sales_order("QTN-IDX", item_indices=[3])


@patch(
    "oneerp_selling_app.services.quotation_conversion_service.resolve_sales_partner_snapshot",
    return_value={
        "sales_partner_id": "SPAR-001",
        "sales_partner_name": "총판A",
        "sales_partner_commission_rate": 7.5,
    },
)
def test_견적_전환시_판매파트너_스냅샷을_저장한다(
    mock_partner_snapshot: MagicMock,
    mock_repos: MagicMock,
):
    """견적→판매주문 전환도 판매파트너 스냅샷을 보존해야 한다."""
    quotation = {
        "_id": "QTN-0007",
        "customer_id": "CUST-007",
        "customer_name": "고객7",
        "docstatus": "submitted",
        "items": [{"item_code": "ITEM-A", "qty": 1, "rate": 1000}],
    }
    mock_repos.find_one.return_value = quotation

    svc = QuotationConversionService(tenant_id="T001")
    result = svc.convert_to_sales_order("QTN-0007")

    assert result["so_id"].startswith("SO-")
    inserted_doc = mock_repos.insert_one.call_args.args[0]
    assert inserted_doc["sales_partner_id"] == "SPAR-001"
    assert inserted_doc["sales_partner_name"] == "총판A"
    assert inserted_doc["sales_partner_commission_rate"] == 7.5


def test_빈_아이템_목록에_인덱스_지정시_에러(mock_repos):
    """BR-SELL-002: 아이템이 없는 견적서에 인덱스를 지정하면 에러."""
    quotation = _submitted_quotation_with_items(0)
    mock_repos.find_one.return_value = quotation

    svc = QuotationConversionService(tenant_id="T001")
    with pytest.raises(OneERPError, match="ERR-SELL-032"):
        svc.convert_to_sales_order("QTN-IDX", item_indices=[0])
