"""검색 서비스 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.errors import OneERPError
from oneerp_portal_core_app.portal.services.search_service import SearchService


class TestSearchService:
    """SearchService 테스트."""

    def test_통합_검색(self, mock_collection: MagicMock) -> None:
        """검색 결과를 반환한다."""
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = [
            {
                "_id": "SIDX-1",
                "title": "판매주문 SO-001",
                "url": "/sales/SO-001",
                "required_permission": "",
                "module": "selling",
            },
        ]
        mock_collection.find.return_value = cursor

        svc = SearchService("T1")
        result = svc.search("판매주문", user_permissions=["*:*"])

        assert len(result) == 1
        assert result[0]["title"] == "판매주문 SO-001"

    def test_권한_필터링(self, mock_collection: MagicMock) -> None:
        """BR-PTL-009: 권한 없는 결과가 제외된다."""
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = [
            {"_id": "SIDX-1", "title": "공개 문서", "required_permission": ""},
            {"_id": "SIDX-2", "title": "비공개 문서", "required_permission": "admin:read"},
        ]
        mock_collection.find.return_value = cursor

        svc = SearchService("T1")
        result = svc.search("문서", user_permissions=["user:read"])

        assert len(result) == 1
        assert result[0]["title"] == "공개 문서"

    def test_자동완성_2자_이상(self, mock_collection: MagicMock) -> None:
        """BR-PTL-015: 2자 이상에서 자동완성이 동작한다."""
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = [
            {
                "_id": "SIDX-1",
                "title": "판매주문",
                "url": "/sales",
                "doc_type": "sales_order",
                "module": "selling",
                "required_permission": "",
            },
        ]
        mock_collection.find.return_value = cursor

        svc = SearchService("T1")
        result = svc.autocomplete("판매", user_permissions=["*:*"])

        assert len(result) == 1
        assert result[0]["title"] == "판매주문"

    def test_자동완성_1자_에러(self, mock_collection: MagicMock) -> None:
        """BR-PTL-015: 1자 입력 시 에러 (ERR-PTL-014)."""
        svc = SearchService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.autocomplete("판", user_permissions=["*:*"])
        assert "ERR-PTL-014" in (exc_info.value.detail or "")

    def test_빈_검색어_에러(self, mock_collection: MagicMock) -> None:
        """빈 검색어 시 에러 (ERR-PTL-013)."""
        svc = SearchService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.search("", user_permissions=["*:*"])
        assert "ERR-PTL-013" in (exc_info.value.detail or "")

    def test_모듈_필터(self, mock_collection: MagicMock) -> None:
        """특정 모듈로 검색 범위를 제한한다."""
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = [
            {"_id": "SIDX-1", "title": "HR 문서", "module": "hr", "required_permission": ""},
        ]
        mock_collection.find.return_value = cursor

        svc = SearchService("T1")
        result = svc.search("HR", user_permissions=["*:*"], module="hr")

        assert len(result) == 1

    def test_와일드카드_권한_통과(self, mock_collection: MagicMock) -> None:
        """와일드카드 권한이 있으면 모든 결과를 반환한다."""
        cursor = MagicMock()
        cursor.skip.return_value.limit.return_value = [
            {"_id": "SIDX-1", "title": "비공개 문서", "required_permission": "admin:secret"},
        ]
        mock_collection.find.return_value = cursor

        svc = SearchService("T1")
        result = svc.search("비공개", user_permissions=["*:*"])

        assert len(result) == 1
