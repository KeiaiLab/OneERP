"""결재 데이터바인딩·알림 서비스 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from oneerp_core.errors import OneERPError

# -- 데이터바인딩 서비스 헬퍼 --


def _make_binding_service() -> tuple:
    """ApprovalDataBindingService와 모킹된 Repository를 반환한다."""
    with patch("oneerp_gateway_app.services.approval_data_binding.Repository") as mock_repo_cls:
        repos: dict[str, MagicMock] = {}

        def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
            repo = MagicMock()
            repos[collection_name] = repo
            return repo

        mock_repo_cls.side_effect = _repo_factory

        from oneerp_gateway_app.services.approval_data_binding import ApprovalDataBindingService

        service = ApprovalDataBindingService(tenant_id="test-tenant")

    return service, repos["approval_templates"]


# ========== 데이터바인딩 테스트 ==========


class Test데이터바인딩:
    """ApprovalDataBindingService 테스트."""

    def test_데이터바인딩_필드_매핑(self) -> None:
        """템플릿의 data_binding_fields에 따라 소스 문서 필드가 올바르게 매핑된다."""
        service, template_repo = _make_binding_service()
        template_repo.find_by_id.return_value = {
            "_id": "TMPL-001",
            "data_binding_fields": [
                {"target_field": "신청자", "source_field": "employee"},
                {"target_field": "총금액", "source_field": "total_amount"},
            ],
        }

        source_doc = {"employee": "EMP-001", "total_amount": 500000}

        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = source_doc
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = service.bind_erp_data("TMPL-001", "expenses", "EC-0001")

        assert result["신청자"] == "EMP-001"
        assert result["총금액"] == 500000

    def test_존재하지_않는_템플릿_에러(self) -> None:
        """존재하지 않는 템플릿 ID를 사용하면 OneERPError가 발생한다."""
        service, template_repo = _make_binding_service()
        template_repo.find_by_id.return_value = None

        with pytest.raises(OneERPError, match="not_found"):
            service.bind_erp_data("TMPL-NONE", "selling", "QTN-0001")

    def test_지원하지_않는_서비스_에러(self) -> None:
        """지원하지 않는 소스 서비스명이면 OneERPError가 발생한다."""
        service, template_repo = _make_binding_service()
        template_repo.find_by_id.return_value = {
            "_id": "TMPL-002",
            "data_binding_fields": [
                {"target_field": "필드A", "source_field": "field_a"},
            ],
        }

        with pytest.raises(OneERPError, match="ERR-APR-004"):
            service.bind_erp_data("TMPL-002", "unknown_service", "DOC-001")

    def test_바인딩_필드_없으면_빈_딕트_반환(self) -> None:
        """data_binding_fields가 비어있으면 빈 딕셔너리를 반환한다."""
        service, template_repo = _make_binding_service()
        template_repo.find_by_id.return_value = {
            "_id": "TMPL-003",
            "data_binding_fields": [],
        }

        result = service.bind_erp_data("TMPL-003", "selling", "QTN-0001")

        assert result == {}

    def test_소스_서비스_호출_실패시_에러(self) -> None:
        """소스 서비스 HTTP 호출이 실패하면 OneERPError가 발생한다."""
        service, template_repo = _make_binding_service()
        template_repo.find_by_id.return_value = {
            "_id": "TMPL-004",
            "data_binding_fields": [
                {"target_field": "필드A", "source_field": "field_a"},
            ],
        }

        with patch("httpx.get") as mock_get:
            import httpx

            mock_get.side_effect = httpx.HTTPError("연결 실패")

            with pytest.raises(OneERPError, match="ERR-APR-005"):
                service.bind_erp_data("TMPL-004", "selling", "QTN-0001")


# ========== 알림 서비스 테스트 ==========


class Test결재알림:
    """ApprovalNotificationService 테스트.

    generate_name은 모듈 레벨 참조이므로 메서드 호출 시점에도
    패치가 활성 상태여야 한다. pytest fixture로 컨텍스트를 유지한다.
    """

    @pytest.fixture
    def notification_ctx(self):
        """패치를 테스트 실행 중 유지하는 fixture."""
        with (
            patch("oneerp_gateway_app.services.approval_notification.Repository") as mock_repo_cls,
            patch("oneerp_gateway_app.services.approval_notification.generate_name") as mock_gen,
        ):
            repos: dict[str, MagicMock] = {}

            def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
                repo = MagicMock()
                repos[collection_name] = repo
                return repo

            mock_repo_cls.side_effect = _repo_factory
            mock_gen.return_value = "NOTIF-001"

            from oneerp_gateway_app.services.approval_notification import (
                ApprovalNotificationService,
            )

            service = ApprovalNotificationService(tenant_id="test-tenant")
            yield service, repos["notifications"], mock_gen

    def test_결재자_알림_생성(self, notification_ctx: tuple) -> None:
        """notify_approver 호출 시 notifications 컬렉션에 레코드가 삽입된다."""
        service, notif_repo, _mock_gen = notification_ctx
        notif_id = service.notify_approver("AR-0001", "EMP-MGR", "request")

        assert notif_id == "NOTIF-001"
        notif_repo.insert.assert_called_once()
        inserted_doc = notif_repo.insert.call_args[0][0]
        assert inserted_doc["recipient"] == "EMP-MGR"
        assert inserted_doc["approval_request_id"] == "AR-0001"
        assert inserted_doc["action_type"] == "request"
        assert inserted_doc["title"] == "[결재] 결재 요청"

    def test_승인_알림_라벨(self, notification_ctx: tuple) -> None:
        """approve 유형의 알림 제목이 올바르게 생성된다."""
        service, notif_repo, _mock_gen = notification_ctx
        service.notify_approver("AR-0002", "EMP-CFO", "approve")

        inserted_doc = notif_repo.insert.call_args[0][0]
        assert inserted_doc["title"] == "[결재] 결재 승인"

    def test_거절_알림_라벨(self, notification_ctx: tuple) -> None:
        """reject 유형의 알림 제목이 올바르게 생성된다."""
        service, notif_repo, _mock_gen = notification_ctx
        service.notify_approver("AR-0003", "EMP-001", "reject")

        inserted_doc = notif_repo.insert.call_args[0][0]
        assert inserted_doc["title"] == "[결재] 결재 반려"

    def test_알림_읽음상태_초기값(self, notification_ctx: tuple) -> None:
        """생성된 알림의 is_read 초기값은 False이다."""
        service, notif_repo, _mock_gen = notification_ctx
        service.notify_approver("AR-0004", "EMP-002", "delegate")

        inserted_doc = notif_repo.insert.call_args[0][0]
        assert inserted_doc["is_read"] is False
