"""게시글 서비스 단위 테스트.

SC-BRD-002: 전사 공지 작성/게시
SC-BRD-003: 필독 공지 게시
SC-BRD-006: 예약 발행
SC-BRD-E001: 권한 없는 사용자 게시글 작성
SC-BRD-E002: manage 권한 없이 필독 설정
SC-BRD-E003: 예약 시각이 현재보다 이전
SC-BRD-E007: 익명 비허용 게시판 익명 글
SC-BRD-E011: 상단 고정 11번째
SC-BRD-E014: 유효하지 않은 카테고리
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_board_app.services.post_service import PostService
from oneerp_core.errors import OneERPError


class TestPostService:
    """PostService 테스트."""

    def test_create_post_즉시게시(self, mock_collection) -> None:
        """SC-BRD-002: 게시글 작성 후 즉시 게시 (status=published)."""
        mock_collection.find_one.return_value = {
            "_id": "BRD-2026-00001",
            "board_name": "공지",
            "categories": ["인사", "총무"],
            "allow_anonymous": False,
            "tenant_id": "T1",
        }
        mock_collection.count_documents.return_value = 0

        svc = PostService("T1")
        result = svc.create_post(
            "BRD-2026-00001",
            {
                "title": "테스트 공지",
                "content": "<p>내용</p>",
                "category": "인사",
                "status": "published",
                "author_id": "EMP-001",
            },
            has_write=True,
        )
        assert result["_id"].startswith("PST-")
        assert result["status"] == "published"
        mock_collection.insert_one.assert_called_once()

    def test_create_post_권한_부족(self, mock_collection) -> None:
        """SC-BRD-E001 / BR-BRD-002: write 권한 없으면 403."""
        svc = PostService("T1")
        with pytest.raises(OneERPError, match="forbidden"):
            svc.create_post("BRD-2026-00001", {"title": "테스트"}, has_write=False)

    def test_create_post_익명_비허용(self, mock_collection) -> None:
        """SC-BRD-E007 / BR-BRD-009: 익명 비허용 게시판에서 익명 글 시도."""
        mock_collection.find_one.return_value = {
            "_id": "BRD-2026-00001",
            "allow_anonymous": False,
            "categories": [],
            "tenant_id": "T1",
        }
        svc = PostService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.create_post(
                "BRD-2026-00001",
                {"title": "익명", "content": "내용", "is_anonymous": True},
                has_write=True,
            )
        assert exc_info.value.error == "ERR-BRD-034"

    def test_create_post_유효하지않은_카테고리(self, mock_collection) -> None:
        """SC-BRD-E014 / BR-BRD-016: 게시판에 없는 카테고리."""
        mock_collection.find_one.return_value = {
            "_id": "BRD-2026-00001",
            "categories": ["인사", "총무", "IT"],
            "allow_anonymous": False,
            "tenant_id": "T1",
        }
        svc = PostService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.create_post(
                "BRD-2026-00001",
                {"title": "테스트", "content": "내용", "category": "재무"},
                has_write=True,
            )
        assert exc_info.value.error == "ERR-BRD-038"

    def test_create_post_필독_권한_부족(self, mock_collection) -> None:
        """SC-BRD-E002 / BR-BRD-004: manage 없이 필독 설정 시 403."""
        mock_collection.find_one.return_value = {
            "_id": "BRD-2026-00001",
            "categories": [],
            "allow_anonymous": False,
            "tenant_id": "T1",
        }
        svc = PostService("T1")
        with pytest.raises(OneERPError, match="forbidden"):
            svc.create_post(
                "BRD-2026-00001",
                {"title": "필독", "content": "내용", "is_must_read": True},
                has_write=True,
                has_manage=False,
            )

    def test_create_post_상단고정_제한(self, mock_collection) -> None:
        """SC-BRD-E011 / BR-BRD-017: 상단 고정 10개 초과 시 422."""
        mock_collection.find_one.return_value = {
            "_id": "BRD-2026-00001",
            "categories": [],
            "allow_anonymous": False,
            "tenant_id": "T1",
        }
        mock_collection.count_documents.return_value = 10

        svc = PostService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.create_post(
                "BRD-2026-00001",
                {"title": "고정", "content": "내용", "is_pinned": True},
                has_write=True,
            )
        assert exc_info.value.error == "ERR-BRD-039"

    def test_create_post_예약발행_과거(self, mock_collection) -> None:
        """SC-BRD-E003 / BR-BRD-006: 예약 시각이 과거."""
        mock_collection.find_one.return_value = {
            "_id": "BRD-2026-00001",
            "categories": [],
            "allow_anonymous": False,
            "tenant_id": "T1",
        }
        svc = PostService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.create_post(
                "BRD-2026-00001",
                {
                    "title": "예약",
                    "content": "내용",
                    "status": "scheduled",
                    "scheduled_at": "2020-01-01T00:00:00+00:00",
                },
                has_write=True,
            )
        assert exc_info.value.error == "ERR-BRD-030"

    def test_update_post_본인(self, mock_collection) -> None:
        """BR-BRD-003: 본인 글 수정 성공."""
        mock_collection.find_one.return_value = {
            "_id": "PST-2026-00001",
            "author_id": "EMP-001",
            "status": "published",
            "revision_count": 0,
            "tenant_id": "T1",
        }
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = PostService("T1")
        result = svc.update_post(
            "PST-2026-00001",
            {"title": "수정된 제목"},
            user_id="EMP-001",
        )
        assert result["_id"] == "PST-2026-00001"
        assert result["revision_count"] == 1

    def test_update_post_타인_권한부족(self, mock_collection) -> None:
        """BR-BRD-003: 타인 글 수정 시 manage 없으면 403."""
        mock_collection.find_one.return_value = {
            "_id": "PST-2026-00001",
            "author_id": "EMP-001",
            "status": "published",
            "tenant_id": "T1",
        }
        svc = PostService("T1")
        with pytest.raises(OneERPError, match="forbidden"):
            svc.update_post(
                "PST-2026-00001",
                {"title": "수정"},
                user_id="EMP-002",
                has_manage=False,
            )

    def test_delete_post_관리자(self, mock_collection) -> None:
        """BR-BRD-003: manage 권한으로 타인 글 삭제."""
        mock_collection.find_one.return_value = {
            "_id": "PST-2026-00001",
            "author_id": "EMP-001",
            "status": "published",
            "tenant_id": "T1",
        }
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = PostService("T1")
        result = svc.delete_post("PST-2026-00001", user_id="ADMIN", has_manage=True)
        assert result is True

    def test_publish_post(self, mock_collection) -> None:
        """게시글 게시 전환."""
        mock_collection.find_one.return_value = {
            "_id": "PST-2026-00001",
            "status": "draft",
            "is_must_read": False,
            "tenant_id": "T1",
        }
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = PostService("T1")
        result = svc.publish_post("PST-2026-00001")
        assert result["status"] == "published"
        assert "published_at" in result

    def test_archive_post(self, mock_collection) -> None:
        """게시글 아카이브 전환."""
        mock_collection.find_one.return_value = {
            "_id": "PST-2026-00001",
            "status": "published",
            "tenant_id": "T1",
        }
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = PostService("T1")
        result = svc.archive_post("PST-2026-00001")
        assert result["status"] == "archived"

    def test_get_post_삭제됨(self, mock_collection) -> None:
        """삭제된 게시글 조회 시 404."""
        mock_collection.find_one.return_value = {
            "_id": "PST-2026-00001",
            "status": "deleted",
            "tenant_id": "T1",
        }
        svc = PostService("T1")
        with pytest.raises(OneERPError, match="not_found"):
            svc.get_post("PST-2026-00001")
