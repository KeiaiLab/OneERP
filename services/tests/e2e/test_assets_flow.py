"""E2E: 자산 플로우 — Asset → DepreciationEntry → Scrap."""

from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.e2e


class TestAssetsFlow:
    """자산 모듈의 전체 사용자 시나리오를 검증한다."""

    def test_자산_생성_제출_폐기(self, gateway_client: httpx.Client) -> None:
        """Asset 생성 → 제출 → 폐기 워크플로우."""
        resp = gateway_client.post(
            "/api/v1/assets",
            json={
                "asset_name": "E2E 테스트 노트북",
                "asset_category": "IT 장비",
                "purchase_date": "2026-01-15",
                "gross_amount": 2000000,
                "depreciation_method": "straight_line",
                "useful_life_years": 5,
                "salvage_value": 200000,
                "current_value": 2000000,
            },
        )
        assert resp.status_code == 201
        asset_id = resp.json()["id"]

        # 조회
        resp = gateway_client.get(f"/api/v1/assets/{asset_id}")
        assert resp.status_code == 200
        asset = resp.json()
        assert asset["asset_name"] == "E2E 테스트 노트북"
        assert asset["gross_amount"] == 2000000

        # 제출
        resp = gateway_client.post(f"/api/v1/assets/{asset_id}/submit")
        assert resp.status_code == 200

        # 폐기
        resp = gateway_client.post(f"/api/v1/assets/{asset_id}/scrap")
        assert resp.status_code == 200

    def test_감가상각_생성_조회(self, gateway_client: httpx.Client) -> None:
        """DepreciationEntry 생성 → 조회."""
        # 자산 생성
        resp = gateway_client.post(
            "/api/v1/assets",
            json={
                "asset_name": "감가상각 테스트 서버",
                "asset_category": "IT 장비",
                "gross_amount": 5000000,
                "depreciation_method": "straight_line",
                "useful_life_years": 5,
                "salvage_value": 500000,
                "current_value": 5000000,
            },
        )
        asset_id = resp.json()["id"]

        # 감가상각 생성
        resp = gateway_client.post(
            "/api/v1/depreciation-entries",
            json={
                "asset_ref": asset_id,
                "posting_date": "2026-03-31",
                "depreciation_amount": 75000,
                "accumulated_depreciation": 75000,
                "remaining_value": 4925000,
            },
        )
        assert resp.status_code == 201
        dep_id = resp.json()["id"]

        # 조회
        resp = gateway_client.get(f"/api/v1/depreciation-entries/{dep_id}")
        assert resp.status_code == 200
        dep = resp.json()
        assert dep["depreciation_amount"] == 75000
        assert dep["remaining_value"] == 4925000

        # 목록
        resp = gateway_client.get("/api/v1/depreciation-entries")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_자산_CRUD(self, gateway_client: httpx.Client) -> None:
        """Asset 생성 → 수정 → 삭제 (초안 상태)."""
        resp = gateway_client.post(
            "/api/v1/assets",
            json={
                "asset_name": "삭제 테스트 자산",
                "asset_category": "가구",
                "gross_amount": 500000,
            },
        )
        asset_id = resp.json()["id"]

        # 수정
        resp = gateway_client.put(
            f"/api/v1/assets/{asset_id}",
            json={
                "asset_name": "수정 삭제 테스트 자산",
            },
        )
        assert resp.status_code == 200

        # 삭제
        resp = gateway_client.delete(f"/api/v1/assets/{asset_id}")
        assert resp.status_code == 204
