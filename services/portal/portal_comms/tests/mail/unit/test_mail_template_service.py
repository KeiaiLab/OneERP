"""메일 템플릿 서비스 단위 테스트.

SC-MAIL-020 ~ SC-MAIL-021, EX-MAIL-020 ~ EX-MAIL-022 시나리오를 검증한다.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from oneerp_core.errors import OneERPError
from oneerp_portal_comms_app.mail.services.mail_template_service import MailTemplateService


class TestMailTemplateService:
    """MailTemplateService 테스트."""

    def test_create_template_정상(self, mock_collection) -> None:
        """SC-MAIL-021: 템플릿 생성 정상 시나리오."""
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value.limit.return_value = []
        mock_collection.find.return_value = mock_cursor

        svc = MailTemplateService("T1")
        result = svc.create_template(
            template_name="환영 메일",
            subject_template="환영합니다, {{name}}님",
            body_template="{{name}}님의 입사를 축하합니다. 부서: {{department}}",
        )
        assert "template_id" in result
        assert "name" in result["variables"]
        assert "department" in result["variables"]

    def test_create_template_이름_중복_에러(self, mock_collection) -> None:
        """EX-MAIL-020: 템플릿명 중복 시 에러."""
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value.limit.return_value = [
            {"_id": "MTPL-2026-00001", "template_name": "환영 메일"},
        ]
        mock_collection.find.return_value = mock_cursor

        svc = MailTemplateService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.create_template(template_name="환영 메일")
        assert "이미 존재합니다" in (exc_info.value.detail or "")

    def test_render_template_정상(self, mock_collection) -> None:
        """SC-MAIL-020: 템플릿 렌더링 정상 시나리오."""
        mock_collection.find_one.return_value = {
            "_id": "MTPL-2026-00001",
            "template_name": "환영 메일",
            "subject_template": "환영합니다, {{name}}님",
            "body_template": "{{name}}님의 입사를 축하합니다.",
            "body_html_template": "<p>{{name}}님 환영합니다</p>",
            "variables": ["name"],
            "is_active": True,
            "usage_count": 0,
            "tenant_id": "T1",
        }
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = MailTemplateService("T1")
        result = svc.render_template(
            template_id="MTPL-2026-00001",
            context={"name": "홍길동"},
        )
        assert result["subject"] == "환영합니다, 홍길동님"
        assert "홍길동" in result["body"]
        assert "홍길동" in result["body_html"]

    def test_render_template_비활성_에러(self, mock_collection) -> None:
        """EX-MAIL-022: 비활성 템플릿 렌더링 시 에러."""
        mock_collection.find_one.return_value = {
            "_id": "MTPL-2026-00001",
            "is_active": False,
            "variables": [],
            "tenant_id": "T1",
        }

        svc = MailTemplateService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.render_template(
                template_id="MTPL-2026-00001",
                context={},
            )
        assert "비활성" in (exc_info.value.detail or "")

    def test_render_template_변수_누락_에러(self, mock_collection) -> None:
        """EX-MAIL-021: 필수 변수 누락 시 에러."""
        mock_collection.find_one.return_value = {
            "_id": "MTPL-2026-00001",
            "is_active": True,
            "subject_template": "{{name}}님",
            "body_template": "",
            "body_html_template": "",
            "variables": ["name", "department"],
            "usage_count": 0,
            "tenant_id": "T1",
        }

        svc = MailTemplateService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.render_template(
                template_id="MTPL-2026-00001",
                context={"name": "홍길동"},
            )
        assert "변수 누락" in (exc_info.value.detail or "")

    def test_render_template_존재하지_않으면_에러(self, mock_collection) -> None:
        """템플릿이 없으면 에러."""
        mock_collection.find_one.return_value = None

        svc = MailTemplateService("T1")
        with pytest.raises(OneERPError) as exc_info:
            svc.render_template(
                template_id="INVALID",
                context={},
            )
        assert "찾을 수 없습니다" in (exc_info.value.detail or "")

    def test_render_template_사용횟수_증가(self, mock_collection) -> None:
        """렌더링 시 usage_count가 증가한다."""
        mock_collection.find_one.return_value = {
            "_id": "MTPL-2026-00001",
            "is_active": True,
            "subject_template": "안녕하세요",
            "body_template": "본문",
            "body_html_template": "",
            "variables": [],
            "usage_count": 5,
            "tenant_id": "T1",
        }
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        svc = MailTemplateService("T1")
        svc.render_template(template_id="MTPL-2026-00001", context={})
        mock_collection.update_one.assert_called_once()
