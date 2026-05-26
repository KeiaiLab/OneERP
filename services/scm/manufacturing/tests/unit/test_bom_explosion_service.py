"""BOM 전개 서비스(BOMExplosionService) 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError


def _make_service() -> tuple:
    with patch(
        "oneerp_manufacturing_app.services.bom_explosion_service.Repository"
    ) as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory
        from oneerp_manufacturing_app.services.bom_explosion_service import BOMExplosionService

        service = BOMExplosionService(tenant_id="test-tenant")
    return service, repos["boms"]


class TestBOM전개:
    def test_단일_레벨_전개(self) -> None:
        """1단계 BOM을 flat 목록으로 전개한다."""
        service, bom_repo = _make_service()
        bom_repo.find_by_id.return_value = {
            "_id": "BOM-001",
            "item_code": "PROD-A",
            "items": [
                {"item_code": "MAT-1", "qty": 2, "uom": "EA"},
                {"item_code": "MAT-2", "qty": 3, "uom": "KG"},
            ],
        }

        result = service.explode_bom("BOM-001", qty=5)

        assert len(result) == 2
        assert result[0]["item_code"] == "MAT-1"
        assert result[0]["qty"] == 10  # 2 * 5
        assert result[1]["qty"] == 15  # 3 * 5

    def test_다단계_재귀_전개(self) -> None:
        """하위 BOM이 있으면 재귀적으로 전개한다."""
        service, bom_repo = _make_service()

        def _find_bom(bom_id: str):
            boms = {
                "BOM-001": {
                    "_id": "BOM-001",
                    "item_code": "PROD-A",
                    "items": [
                        {"item_code": "SEMI-1", "qty": 2, "bom_id": "BOM-002"},
                    ],
                },
                "BOM-002": {
                    "_id": "BOM-002",
                    "item_code": "SEMI-1",
                    "items": [
                        {"item_code": "RAW-1", "qty": 3, "uom": "EA"},
                    ],
                },
            }
            return boms.get(bom_id)

        bom_repo.find_by_id.side_effect = _find_bom

        result = service.explode_bom("BOM-001", qty=1)

        # SEMI-1의 BOM이 있으므로 RAW-1만 나와야 함
        assert len(result) == 1
        assert result[0]["item_code"] == "RAW-1"
        assert result[0]["qty"] == 6  # 2 * 3
        assert result[0]["level"] == 2

    def test_최대_깊이_제한(self) -> None:
        """max_depth를 넘으면 전개를 중단한다."""
        service, bom_repo = _make_service()
        # 순환 BOM — 자기 자신을 참조
        bom_repo.find_by_id.return_value = {
            "_id": "BOM-LOOP",
            "item_code": "LOOP",
            "items": [
                {"item_code": "LOOP", "qty": 1, "bom_id": "BOM-LOOP"},
            ],
        }

        result = service.explode_bom("BOM-LOOP", qty=1, max_depth=3)

        # 무한루프 없이 결과가 비어있어야 함 (말단 자재 없음)
        assert len(result) == 0

    def test_미존재_BOM_빈결과(self) -> None:
        """존재하지 않는 BOM이면 빈 목록."""
        service, bom_repo = _make_service()
        bom_repo.find_by_id.return_value = None

        result = service.explode_bom("BOM-999")

        assert result == []


class TestBOM트리:
    def test_트리_구성(self) -> None:
        """nested dict 트리를 생성한다."""
        service, bom_repo = _make_service()
        bom_repo.find_by_id.return_value = {
            "_id": "BOM-001",
            "item_code": "PROD-A",
            "items": [
                {"item_code": "MAT-1", "qty": 2, "uom": "EA"},
            ],
        }

        tree = service.get_bom_tree("BOM-001")

        assert tree["item_code"] == "PROD-A"
        assert len(tree["children"]) == 1
        assert tree["children"][0]["item_code"] == "MAT-1"

    def test_미존재_BOM_에러(self) -> None:
        """BOM 미존재 시 OneERPError(ERR-MFG-001)."""
        service, bom_repo = _make_service()
        bom_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="ERR-MFG-001"):
            service.get_bom_tree("BOM-999")


class Test전개_단가포함:
    def test_전개결과에_rate_포함(self) -> None:
        """explode_bom() 결과 각 항목에 rate(단가)가 포함되어야 한다."""
        service, bom_repo = _make_service()
        bom_repo.find_by_id.return_value = {
            "_id": "BOM-001",
            "item_code": "PROD-A",
            "items": [
                {"item_code": "MAT-1", "qty": 2, "uom": "EA", "unit_price": 100},
            ],
        }

        result = service.explode_bom("BOM-001", qty=1)

        assert result[0]["rate"] == 100.0

    def test_단가없는_항목_rate_0(self) -> None:
        """unit_price가 없는 자재는 rate=0."""
        service, bom_repo = _make_service()
        bom_repo.find_by_id.return_value = {
            "_id": "BOM-001",
            "item_code": "PROD-A",
            "items": [
                {"item_code": "MAT-1", "qty": 1, "uom": "EA"},
            ],
        }

        result = service.explode_bom("BOM-001", qty=1)

        assert result[0]["rate"] == 0.0


class Test원가계산:
    def test_단가_기반_총원가(self) -> None:
        """전개 결과에 단가를 곱해 총원가를 산출한다."""
        service, bom_repo = _make_service()
        bom_repo.find_by_id.return_value = {
            "_id": "BOM-001",
            "item_code": "PROD-A",
            "items": [
                {"item_code": "MAT-1", "qty": 2, "uom": "EA", "unit_price": 100},
                {"item_code": "MAT-2", "qty": 1, "uom": "KG", "unit_price": 500},
            ],
        }

        result = service.calculate_cost("BOM-001", qty=3)

        # MAT-1: 2*3*100=600, MAT-2: 1*3*500=1500 → 총 2100
        assert result["total_cost"] == 2100
        assert len(result["items"]) == 2

    def test_다단계_BOM_원가_산출(self) -> None:
        """하위 BOM 자재의 단가도 올바르게 적용되어야 한다 (버그 수정 검증)."""
        service, bom_repo = _make_service()

        def _find_bom(bom_id: str):
            boms = {
                "BOM-001": {
                    "_id": "BOM-001",
                    "item_code": "PROD-A",
                    "items": [
                        {"item_code": "MAT-1", "qty": 1, "uom": "EA", "unit_price": 200},
                        {"item_code": "SEMI-1", "qty": 2, "bom_id": "BOM-002"},
                    ],
                },
                "BOM-002": {
                    "_id": "BOM-002",
                    "item_code": "SEMI-1",
                    "items": [
                        {"item_code": "RAW-1", "qty": 3, "uom": "EA", "unit_price": 50},
                        {"item_code": "RAW-2", "qty": 1, "uom": "KG", "unit_price": 80},
                    ],
                },
            }
            return boms.get(bom_id)

        bom_repo.find_by_id.side_effect = _find_bom

        result = service.calculate_cost("BOM-001", qty=1)

        # MAT-1: 1*200=200
        # RAW-1: 2*3*50=300 (하위 BOM에서 전개)
        # RAW-2: 2*1*80=160 (하위 BOM에서 전개)
        # 총원가 = 200 + 300 + 160 = 660
        assert result["total_cost"] == 660
        assert len(result["items"]) == 3

        # 하위 BOM 자재의 단가가 0이 아님을 검증 (이전 버그)
        raw1 = next(i for i in result["items"] if i["item_code"] == "RAW-1")
        assert raw1["unit_price"] == 50
        assert raw1["cost"] == 300

        raw2 = next(i for i in result["items"] if i["item_code"] == "RAW-2")
        assert raw2["unit_price"] == 80
        assert raw2["cost"] == 160
