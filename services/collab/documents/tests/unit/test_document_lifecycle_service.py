"""문서 생명주기 서비스 단위 테스트.

SC-DOC-001~005: 문서 생성, 수정, 제출, 승인, 배포 테스트.
EX-DOC-001~011: 에러 케이스 테스트.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from oneerp_core.errors import OneERPError
from oneerp_documents_app.services.document_lifecycle_service import (
    DocumentLifecycleService,
    _compute_content_hash,
    _compute_document_hash,
    _strip_html,
)

# 이전 정규식은 이 길이에서 O(n²) 로 수 초 걸렸다.
_REDOS_INPUT_LEN = 100_000
_REDOS_BUDGET_SEC = 1.0


class TestDocumentLifecycleService:
    """DocumentLifecycleService 테스트."""

    # ──────────────────────────────────────────────
    # 문서 생성 (SC-DOC-001)
    # ──────────────────────────────────────────────

    def test_문서_생성(self, mock_collection: MagicMock) -> None:
        """SC-DOC-001: 문서를 생성하면 draft 상태, version=1이다."""
        mock_collection.find_one.return_value = None
        mock_collection.insert_one.return_value = MagicMock(inserted_id="DOC-0001")

        svc = DocumentLifecycleService("T1")
        result = svc.create_document(
            title="테스트 문서",
            category="DC-T001-00001",
            content="<p>내용</p>",
            author="EMP-001",
        )

        assert result["title"] == "테스트 문서"
        assert result["status"] == "draft"
        assert result["version"] == 1
        assert result["content_plain"] == "내용"

    def test_문서_생성_태그_초과(self, mock_collection: MagicMock) -> None:
        """태그 30개 초과 시 에러를 발생시킨다."""
        svc = DocumentLifecycleService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.create_document(
                title="테스트",
                category="DC-001",
                tags=[f"tag{i}" for i in range(31)],
                author="EMP-001",
            )
        assert exc_info.value.status_code == 400

    # ──────────────────────────────────────────────
    # 문서 수정 (SC-DOC-002)
    # ──────────────────────────────────────────────

    def test_문서_수정_버전_증가(self, mock_collection: MagicMock) -> None:
        """SC-DOC-002: 내용 변경 시 버전이 자동 증가한다."""
        mock_collection.find_one.return_value = {
            "_id": "DOC-0001",
            "title": "원본",
            "content": "<p>원본</p>",
            "status": "draft",
            "version": 1,
            "is_locked": False,
            "tenant_id": "T1",
        }
        mock_collection.update_one.return_value = MagicMock(modified_count=1)
        mock_collection.insert_one.return_value = MagicMock()
        # find_many (서명 검사): 서명 없음
        mock_collection.find.return_value.skip.return_value.limit.return_value = []

        svc = DocumentLifecycleService("T1")
        result = svc.update_document(
            "DOC-0001",
            actor="EMP-001",
            content="<p>수정됨</p>",
            change_summary="내용 수정",
        )

        assert result["version"] == 2

    def test_문서_수정_잠금_충돌(self, mock_collection: MagicMock) -> None:
        """EX-DOC-003: 다른 사용자가 체크아웃한 문서 수정 시 409 에러."""
        mock_collection.find_one.return_value = {
            "_id": "DOC-0001",
            "status": "draft",
            "is_locked": True,
            "locked_by": "EMP-002",
            "tenant_id": "T1",
        }
        # find_many (서명 검사): 서명 없음
        mock_collection.find.return_value.skip.return_value.limit.return_value = []

        svc = DocumentLifecycleService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.update_document("DOC-0001", actor="EMP-001", title="수정")
        assert exc_info.value.status_code == 409
        assert "ERR-DOC-008" in (exc_info.value.detail or "")

    def test_문서_수정_서명후_금지(self, mock_collection: MagicMock) -> None:
        """EX-DOC-011: 전자서명 완료 후 편집 시 409 에러 (ERR-DOC-016)."""
        mock_collection.find_one.return_value = {
            "_id": "DOC-0001",
            "status": "approved",
            "is_locked": False,
            "tenant_id": "T1",
        }
        # find_many (서명 검사): 유효한 서명 존재
        mock_collection.find.return_value.skip.return_value.limit.return_value = [
            {"_id": "SG-0001", "is_valid": True}
        ]

        svc = DocumentLifecycleService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.update_document("DOC-0001", actor="EMP-001", title="수정")
        assert exc_info.value.status_code == 409
        assert "ERR-DOC-016" in (exc_info.value.detail or "")

    # ──────────────────────────────────────────────
    # 상태 전이 (SC-DOC-003~005)
    # ──────────────────────────────────────────────

    def test_문서_제출(self, mock_collection: MagicMock) -> None:
        """SC-DOC-003: draft → review 전이."""
        mock_collection.find_one.return_value = {
            "_id": "DOC-0001",
            "status": "draft",
            "title": "보고서",
            "content": "내용",
            "tenant_id": "T1",
        }
        mock_collection.update_one.return_value = MagicMock(modified_count=1)
        mock_collection.insert_one.return_value = MagicMock()

        svc = DocumentLifecycleService("T1")
        result = svc.submit_document("DOC-0001", actor="EMP-001")

        assert result["status"] == "review"

    def test_문서_승인(self, mock_collection: MagicMock) -> None:
        """SC-DOC-004: review → approved 전이."""
        mock_collection.find_one.return_value = {
            "_id": "DOC-0001",
            "status": "review",
            "tenant_id": "T1",
        }
        mock_collection.update_one.return_value = MagicMock(modified_count=1)
        mock_collection.insert_one.return_value = MagicMock()

        svc = DocumentLifecycleService("T1")
        result = svc.approve_document("DOC-0001", actor="EMP-002")

        assert result["status"] == "approved"

    def test_문서_배포(self, mock_collection: MagicMock) -> None:
        """SC-DOC-005: approved → published 전이."""
        mock_collection.find_one.return_value = {
            "_id": "DOC-0001",
            "status": "approved",
            "version": 2,
            "title": "보고서",
            "content": "내용",
            "category": "DC-001",
            "retention_policy": None,
            "tenant_id": "T1",
        }
        mock_collection.update_one.return_value = MagicMock(modified_count=1)
        mock_collection.insert_one.return_value = MagicMock()

        svc = DocumentLifecycleService("T1")
        result = svc.publish_document("DOC-0001", actor="EMP-001")

        assert result["status"] == "published"
        assert result["version"] == 3

    def test_문서_반려(self, mock_collection: MagicMock) -> None:
        """review → draft 반려 전이."""
        mock_collection.find_one.return_value = {
            "_id": "DOC-0001",
            "status": "review",
            "tenant_id": "T1",
        }
        mock_collection.update_one.return_value = MagicMock(modified_count=1)
        mock_collection.insert_one.return_value = MagicMock()

        svc = DocumentLifecycleService("T1")
        result = svc.reject_document("DOC-0001", actor="EMP-002", reason="보완 필요")

        assert result["status"] == "draft"

    def test_잘못된_상태_전이(self, mock_collection: MagicMock) -> None:
        """잘못된 상태 전이 시 ERR-DOC-030 에러."""
        mock_collection.find_one.return_value = {
            "_id": "DOC-0001",
            "status": "draft",
            "tenant_id": "T1",
        }

        svc = DocumentLifecycleService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.approve_document("DOC-0001", actor="EMP-001")
        assert exc_info.value.status_code == 422
        assert "ERR-DOC-030" in exc_info.value.error

    def test_폐기_상태에서_전이_불가(self, mock_collection: MagicMock) -> None:
        """disposed 상태에서는 어떤 전이도 불가."""
        mock_collection.find_one.return_value = {
            "_id": "DOC-0001",
            "status": "disposed",
            "tenant_id": "T1",
        }

        svc = DocumentLifecycleService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.publish_document("DOC-0001", actor="EMP-001")
        assert exc_info.value.status_code == 422

    # ──────────────────────────────────────────────
    # 체크아웃/체크인 (SC-DOC-011)
    # ──────────────────────────────────────────────

    def test_체크아웃(self, mock_collection: MagicMock) -> None:
        """문서 체크아웃 성공."""
        mock_collection.find_one.return_value = {
            "_id": "DOC-0001",
            "is_locked": False,
            "tenant_id": "T1",
        }
        mock_collection.update_one.return_value = MagicMock(modified_count=1)
        mock_collection.insert_one.return_value = MagicMock()

        svc = DocumentLifecycleService("T1")
        result = svc.checkout_document("DOC-0001", actor="EMP-001")

        assert result["is_locked"] is True
        assert result["locked_by"] == "EMP-001"

    def test_체크아웃_중복_잠금(self, mock_collection: MagicMock) -> None:
        """이미 잠금된 문서 체크아웃 시 409 에러 (ERR-DOC-008)."""
        mock_collection.find_one.return_value = {
            "_id": "DOC-0001",
            "is_locked": True,
            "locked_by": "EMP-002",
            "tenant_id": "T1",
        }

        svc = DocumentLifecycleService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.checkout_document("DOC-0001", actor="EMP-001")
        assert exc_info.value.status_code == 409

    def test_체크인(self, mock_collection: MagicMock) -> None:
        """문서 체크인 성공."""
        mock_collection.find_one.return_value = {
            "_id": "DOC-0001",
            "is_locked": True,
            "locked_by": "EMP-001",
            "tenant_id": "T1",
        }
        mock_collection.update_one.return_value = MagicMock(modified_count=1)
        mock_collection.insert_one.return_value = MagicMock()

        svc = DocumentLifecycleService("T1")
        result = svc.checkin_document("DOC-0001", actor="EMP-001")

        assert result["is_locked"] is False

    # ──────────────────────────────────────────────
    # 소프트 삭제 (BR-DOC-010, BR-DOC-011)
    # ──────────────────────────────────────────────

    def test_소프트_삭제(self, mock_collection: MagicMock) -> None:
        """문서 소프트 삭제 성공."""
        mock_collection.find_one.return_value = {
            "_id": "DOC-0001",
            "retention_until": None,
            "tenant_id": "T1",
        }
        mock_collection.update_one.return_value = MagicMock(modified_count=1)
        mock_collection.insert_one.return_value = MagicMock()

        svc = DocumentLifecycleService("T1")
        result = svc.soft_delete_document("DOC-0001", actor="EMP-001")

        assert result["is_deleted"] is True

    def test_보존기간_내_삭제_금지(self, mock_collection: MagicMock) -> None:
        """EX-DOC-010: 보존 기간 내 삭제 시 ERR-DOC-011 에러."""
        future_date = datetime(2030, 1, 1, tzinfo=UTC)
        mock_collection.find_one.return_value = {
            "_id": "DOC-0001",
            "retention_until": future_date,
            "tenant_id": "T1",
        }

        svc = DocumentLifecycleService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.soft_delete_document("DOC-0001", actor="EMP-001")
        assert exc_info.value.status_code == 422
        assert "ERR-DOC-011" in exc_info.value.error

    # ──────────────────────────────────────────────
    # 버전 복원 (SC-DOC-010)
    # ──────────────────────────────────────────────

    def test_버전_복원(self, mock_collection: MagicMock) -> None:
        """SC-DOC-010: 특정 버전에서 문서를 복원한다."""
        mock_collection.find_one.return_value = {
            "_id": "DOC-0001",
            "version": 5,
            "title": "현재 제목",
            "content": "현재 내용",
            "tenant_id": "T1",
        }
        # find_many (버전 조회): find().skip().limit()
        mock_collection.find.return_value.skip.return_value.limit.return_value = [
            {
                "_id": "DV-0002",
                "version_no": 2,
                "title": "v2 제목",
                "content": "<p>v2 내용</p>",
                "file_attachments": [],
            }
        ]
        mock_collection.update_one.return_value = MagicMock(modified_count=1)
        mock_collection.insert_one.return_value = MagicMock()

        svc = DocumentLifecycleService("T1")
        result = svc.restore_version("DOC-0001", 2, actor="EMP-001")

        assert result["version"] == 6
        assert result["title"] == "v2 제목"

    # ──────────────────────────────────────────────
    # 유틸리티 함수
    # ──────────────────────────────────────────────

    def test_HTML_태그_제거(self) -> None:
        """HTML 태그를 제거하여 플레인텍스트로 변환한다."""
        assert _strip_html("<p>안녕하세요</p>") == "안녕하세요"
        assert _strip_html("<b>굵은</b> <i>기울임</i>") == "굵은 기울임"
        assert _strip_html("") == ""

    def test_HTML_태그_제거_ReDoS_방지(self) -> None:
        """'<' 반복 입력도 선형 시간에 처리한다 (py/polynomial-redos)."""
        adversarial = "<" * _REDOS_INPUT_LEN

        started = time.perf_counter()
        result = _strip_html(adversarial)
        elapsed = time.perf_counter() - started

        assert result == adversarial
        assert elapsed < _REDOS_BUDGET_SEC

    def test_문서_해시_계산(self) -> None:
        """동일 입력 시 동일한 SHA-256 해시를 반환한다."""
        h1 = _compute_document_hash("제목", "내용", ["checksum1"])
        h2 = _compute_document_hash("제목", "내용", ["checksum1"])
        assert h1 == h2
        assert len(h1) == 64

    def test_콘텐츠_해시_계산(self) -> None:
        """콘텐츠 해시가 일관되게 계산된다."""
        h1 = _compute_content_hash("제목", "내용")
        h2 = _compute_content_hash("제목", "내용")
        assert h1 == h2

    def test_문서_미존재_404(self, mock_collection: MagicMock) -> None:
        """존재하지 않는 문서 조회 시 404 에러 (ERR-DOC-040)."""
        mock_collection.find_one.return_value = None

        svc = DocumentLifecycleService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.submit_document("DOC-9999", actor="EMP-001")
        assert exc_info.value.status_code == 404
