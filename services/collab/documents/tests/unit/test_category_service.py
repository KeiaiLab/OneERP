"""문서 분류 서비스 단위 테스트.

BR-DOC-018: 소속 문서 존재 시 삭제 제한.
BR-DOC-019: 최대 10단계 계층 깊이 제한.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.errors import OneERPError
from oneerp_documents_app.services.category_service import CategoryService


class TestCategoryService:
    """CategoryService 테스트."""

    def test_루트_카테고리_깊이_경로(self, mock_collection: MagicMock) -> None:
        """루트 카테고리의 깊이는 0, 경로는 /."""
        svc = CategoryService("T1")
        depth, path = svc.calculate_depth_and_path(None)

        assert depth == 0
        assert path == "/"

    def test_하위_카테고리_깊이_경로(self, mock_collection: MagicMock) -> None:
        """하위 카테고리의 깊이와 경로를 올바르게 계산한다."""
        mock_collection.find_one.return_value = {
            "_id": "DC-001",
            "name": "영업",
            "depth": 0,
            "path": "/",
            "tenant_id": "T1",
        }

        svc = CategoryService("T1")
        depth, path = svc.calculate_depth_and_path("DC-001")

        assert depth == 1
        assert "영업" in path

    def test_계층_깊이_초과(self, mock_collection: MagicMock) -> None:
        """BR-DOC-019: 10단계 초과 시 ERR-DOC-019 에러."""
        mock_collection.find_one.return_value = {
            "_id": "DC-999",
            "name": "깊은분류",
            "depth": 9,
            "path": "/a/b/c/d/e/f/g/h/i/",
            "tenant_id": "T1",
        }

        svc = CategoryService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.calculate_depth_and_path("DC-999")
        assert exc_info.value.status_code == 422
        assert "ERR-DOC-019" in exc_info.value.error

    def test_소속문서_존재시_삭제_거부(self, mock_collection: MagicMock) -> None:
        """BR-DOC-018: 소속 문서가 있으면 삭제를 거부한다."""
        mock_collection.count_documents.return_value = 15

        svc = CategoryService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.validate_delete("DC-001")
        assert exc_info.value.status_code == 400
        assert "ERR-DOC-018" in (exc_info.value.detail or "")

    def test_소속문서_없으면_삭제_허용(self, mock_collection: MagicMock) -> None:
        """소속 문서와 하위 분류가 없으면 삭제를 허용한다."""
        mock_collection.count_documents.return_value = 0

        svc = CategoryService("T1")
        # 에러가 발생하지 않으면 성공
        svc.validate_delete("DC-001")

    def test_상위_카테고리_미존재(self, mock_collection: MagicMock) -> None:
        """존재하지 않는 상위 카테고리 시 404 에러."""
        mock_collection.find_one.return_value = None

        svc = CategoryService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.calculate_depth_and_path("DC-INVALID")
        assert exc_info.value.status_code == 404
