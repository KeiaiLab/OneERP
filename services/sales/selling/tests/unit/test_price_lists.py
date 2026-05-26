"""가격표(PriceList) 워크벤치 엔드포인트 테스트."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

_BASE_URL = "/api/v1/price-lists"


def test_가격표_생성_정상(mock_collection: MagicMock, test_client: MagicMock) -> None:
    """POST /api/v1/price-lists -- 정상 생성 시 201과 _id를 반환한다."""
    mock_collection.insert_one.return_value = MagicMock(inserted_id="PLT-2026-00001")
    response = test_client.post(
        _BASE_URL,
        json={
            "price_list_name": "표준 소매가",
            "currency": "KRW",
            "selling": True,
            "customer_group": "VIP",
            "valid_from": "2026-04-01",
            "valid_to": "2026-04-30",
            "items": [
                {
                    "item_code": "ITEM-001",
                    "item_name": "테스트 품목",
                    "price": "120000",
                    "min_qty": "1",
                },
            ],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["_id"] == "PLT-2026-00001"
    assert data["customer_group"] == "VIP"


@patch("oneerp_selling_app.routes.price_lists._get_pos_profile_repo")
@patch("oneerp_selling_app.routes.price_lists._get_quotation_repo")
@patch("oneerp_selling_app.routes.price_lists._get_customer_group_repo")
@patch("oneerp_selling_app.routes.price_lists._get_price_list_repo")
def test_가격표_목록은_워크벤치_요약과_상태배지를_반환한다(
    mock_get_price_list_repo: MagicMock,
    mock_get_customer_group_repo: MagicMock,
    mock_get_quotation_repo: MagicMock,
    mock_get_pos_profile_repo: MagicMock,
    test_client: MagicMock,
) -> None:
    """가격표 목록은 고객군/만료/사용현황을 요약한 워크벤치 응답을 제공해야 한다."""
    price_list_repo = MagicMock()
    customer_group_repo = MagicMock()
    quotation_repo = MagicMock()
    pos_profile_repo = MagicMock()
    mock_get_price_list_repo.return_value = price_list_repo
    mock_get_customer_group_repo.return_value = customer_group_repo
    mock_get_quotation_repo.return_value = quotation_repo
    mock_get_pos_profile_repo.return_value = pos_profile_repo

    today = datetime.now(UTC).date()
    price_list_repo.find_many.return_value = [
        {
            "_id": "PLT-EXP",
            "price_list_name": "VIP 만료임박",
            "currency": "USD",
            "is_active": True,
            "customer_group": "VIP",
            "valid_from": today.isoformat(),
            "valid_to": (today + timedelta(days=2)).isoformat(),
            "items": [
                {"item_code": "ITEM-A", "item_name": "프리미엄 A", "price": 125, "min_qty": 1},
                {"item_code": "ITEM-A", "item_name": "프리미엄 A", "price": 118, "min_qty": 10},
            ],
        },
        {
            "_id": "PLT-INACTIVE",
            "price_list_name": "비활성 가격표",
            "currency": "KRW",
            "is_active": False,
            "items": [{"item_code": "ITEM-B", "item_name": "표준 B", "price": 9000, "min_qty": 1}],
        },
    ]
    customer_group_repo.find_many.side_effect = lambda query=None, limit=1000, sort=None, skip=0: (
        [{"_id": "CGR-001", "default_price_list": "PLT-EXP"}]
        if query == {"default_price_list": "PLT-EXP"}
        else []
    )
    quotation_repo.find_many.side_effect = lambda query=None, limit=1000, sort=None, skip=0: (
        [{"_id": "QTN-001", "docstatus": 1, "price_list_id": "PLT-EXP"}]
        if query == {"price_list_id": "PLT-EXP"}
        else []
    )
    pos_profile_repo.find_many.side_effect = lambda query=None, limit=1000, sort=None, skip=0: (
        [{"_id": "POS-001", "price_list": "PLT-EXP"}] if query == {"price_list": "PLT-EXP"} else []
    )

    response = test_client.get(f"{_BASE_URL}?status_badge=expiring_soon")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["summary"]["active_count"] == 1
    assert data["summary"]["inactive_count"] == 1
    assert data["summary"]["expiring_soon_count"] == 1
    assert data["summary"]["customer_group_bound_count"] == 1
    assert data["summary"]["quotation_usage_count"] == 1
    assert data["summary"]["total_item_count"] == 3
    row = data["data"][0]
    assert row["status_badge"] == "expiring_soon"
    assert row["recommended_action"] == "review_validity"
    assert row["usage_summary"]["quotation_count"] == 1
    assert row["usage_summary"]["tiered_item_count"] == 1
    assert row["rate_summary"]["max_price"] == 125.0
    assert row["rate_summary"]["min_price"] == 118.0
    assert "open_customer_groups" in row["available_actions"]
    assert "open_catalog_preview" in row["available_actions"]


@patch("oneerp_selling_app.routes.price_lists._get_pos_profile_repo")
@patch("oneerp_selling_app.routes.price_lists._get_quotation_repo")
@patch("oneerp_selling_app.routes.price_lists._get_customer_group_repo")
@patch("oneerp_selling_app.routes.price_lists._get_price_list_repo")
def test_가격표_상세는_단가커버리지와_사용요약을_반환한다(
    mock_get_price_list_repo: MagicMock,
    mock_get_customer_group_repo: MagicMock,
    mock_get_quotation_repo: MagicMock,
    mock_get_pos_profile_repo: MagicMock,
    test_client: MagicMock,
) -> None:
    """가격표 상세는 가격 커버리지와 사용처 요약을 함께 제공해야 한다."""
    price_list_repo = MagicMock()
    customer_group_repo = MagicMock()
    quotation_repo = MagicMock()
    pos_profile_repo = MagicMock()
    mock_get_price_list_repo.return_value = price_list_repo
    mock_get_customer_group_repo.return_value = customer_group_repo
    mock_get_quotation_repo.return_value = quotation_repo
    mock_get_pos_profile_repo.return_value = pos_profile_repo

    today = datetime.now(UTC).date()
    price_list_repo.find_by_id.return_value = {
        "_id": "PLT-001",
        "price_list_name": "VIP USD",
        "currency": "USD",
        "is_active": True,
        "customer_group": "VIP",
        "valid_from": today.isoformat(),
        "valid_to": (today + timedelta(days=14)).isoformat(),
        "items": [
            {"item_code": "ITEM-A", "item_name": "프리미엄 A", "price": 120, "min_qty": 1},
            {"item_code": "ITEM-A", "item_name": "프리미엄 A", "price": 110, "min_qty": 20},
            {"item_code": "ITEM-B", "item_name": "표준 B", "price": 95, "min_qty": 1},
        ],
    }
    customer_group_repo.find_many.return_value = [
        {"_id": "CGR-001", "default_price_list": "PLT-001"}
    ]
    quotation_repo.find_many.return_value = [
        {"_id": "QTN-001", "docstatus": 1, "price_list_id": "PLT-001"},
        {"_id": "QTN-002", "docstatus": 0, "price_list_id": "PLT-001"},
    ]
    pos_profile_repo.find_many.return_value = [{"_id": "POS-001", "price_list": "PLT-001"}]

    response = test_client.get(f"{_BASE_URL}/PLT-001")

    assert response.status_code == 200
    data = response.json()
    assert data["status_badge"] == "active_in_use"
    assert data["usage_summary"] == {
        "customer_group_count": 1,
        "quotation_count": 2,
        "active_quotation_count": 1,
        "pos_profile_count": 1,
        "total_item_count": 3,
        "tiered_item_count": 1,
    }
    assert data["rate_summary"] == {
        "currency": "USD",
        "item_count": 3,
        "tiered_item_count": 1,
        "min_price": 95.0,
        "max_price": 120.0,
    }
    assert data["recommended_action"] == "review_quote_usage"
    assert "edit" in data["available_actions"]
    assert "open_quotations" in data["available_actions"]
    assert "open_pos_profiles" in data["available_actions"]


@patch("oneerp_selling_app.routes.price_lists.PriceListService")
def test_가격표_카탈로그는_고객군_통화_거래일_기준으로_필터링된다(
    mock_price_list_service_cls: MagicMock,
    test_client: MagicMock,
) -> None:
    """적용 가능한 활성 가격표만 고객군/통화/기간 기준으로 반환해야 한다."""
    service = MagicMock()
    mock_price_list_service_cls.return_value = service
    service.catalog.return_value = [
        {
            "_id": "PLT-VIP-USD",
            "id": "PLT-VIP-USD",
            "price_list_name": "VIP USD",
            "customer_group": "VIP",
            "currency": "USD",
            "is_active": True,
            "valid_from": datetime(2026, 4, 1, tzinfo=UTC),
            "valid_to": datetime(2026, 4, 30, tzinfo=UTC),
            "items": [{"item_code": "ITEM-USD", "price": 120}],
        },
    ]

    response = test_client.get(
        f"{_BASE_URL}/catalog?customer_group=VIP&currency=USD&transaction_date=2026-04-09"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["data"][0]["id"] == "PLT-VIP-USD"
    assert data["data"][0]["item_count"] == 1


@patch("oneerp_selling_app.routes.price_lists._get_pos_profile_repo")
@patch("oneerp_selling_app.routes.price_lists._get_quotation_repo")
@patch("oneerp_selling_app.routes.price_lists._get_customer_group_repo")
@patch("oneerp_selling_app.routes.price_lists._get_price_list_repo")
def test_참조된_가격표는_삭제할_수_없다(
    mock_get_price_list_repo: MagicMock,
    mock_get_customer_group_repo: MagicMock,
    mock_get_quotation_repo: MagicMock,
    mock_get_pos_profile_repo: MagicMock,
    test_client: MagicMock,
) -> None:
    """고객그룹/견적/채널에서 사용 중인 가격표는 삭제를 차단해야 한다."""
    price_list_repo = MagicMock()
    customer_group_repo = MagicMock()
    quotation_repo = MagicMock()
    pos_profile_repo = MagicMock()
    mock_get_price_list_repo.return_value = price_list_repo
    mock_get_customer_group_repo.return_value = customer_group_repo
    mock_get_quotation_repo.return_value = quotation_repo
    mock_get_pos_profile_repo.return_value = pos_profile_repo

    price_list_repo.find_by_id.return_value = {
        "_id": "PLT-001",
        "price_list_name": "VIP 가격표",
        "docstatus": 0,
    }
    customer_group_repo.find_many.return_value = [
        {"_id": "CGR-001", "group_name": "VIP", "default_price_list": "PLT-001"},
    ]
    quotation_repo.find_many.return_value = []
    pos_profile_repo.find_many.return_value = []

    response = test_client.delete(f"{_BASE_URL}/PLT-001")

    assert response.status_code == 422
    assert response.json()["error"] == "ERR-SELL-044"
