"""메일 템플릿 서비스 -- 템플릿 관리 및 렌더링 비즈니스 로직.

BR-MAIL-020: 템플릿명은 테넌트 내에서 고유해야 한다.
BR-MAIL-021: 템플릿 변수는 {{변수명}} 형식으로 정의한다.
BR-MAIL-022: 비활성 템플릿은 렌더링 불가.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from oneerp_core.errors import raise_bad_request, raise_conflict, raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

# {{변수명}} 패턴
_VARIABLE_PATTERN = re.compile(r"\{\{(\w+)\}\}")


class MailTemplateService:
    """메일 템플릿 비즈니스 로직.

    SC-MAIL-020: 템플릿 렌더링 정상 시나리오
    SC-MAIL-021: 템플릿 생성 정상 시나리오
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._template_repo = Repository("mail_templates", tenant_id=tenant_id)

    def create_template(
        self,
        *,
        template_name: str,
        subject_template: str = "",
        body_template: str = "",
        body_html_template: str = "",
        category: str = "",
        description: str = "",
    ) -> dict[str, Any]:
        """메일 템플릿을 생성한다.

        BR-MAIL-020: 템플릿명 중복 검증.
        BR-MAIL-021: 템플릿에서 변수 목록 자동 추출.

        EX-MAIL-020: 템플릿명 중복 시 에러.
        """
        # BR-MAIL-020: 중복 검증
        existing = self._template_repo.find_many(
            {"template_name": template_name},
            limit=1,
        )
        if existing:
            raise_conflict(f"템플릿명 '{template_name}'이(가) 이미 존재합니다 [ERR-MAIL-020]")

        # BR-MAIL-021: 변수 자동 추출
        all_text = f"{subject_template} {body_template} {body_html_template}"
        variables = sorted(set(_VARIABLE_PATTERN.findall(all_text)))

        template_id = generate_name("MTPL", tenant_id=self._tenant_id)
        doc = {
            "_id": template_id,
            "template_name": template_name,
            "subject_template": subject_template,
            "body_template": body_template,
            "body_html_template": body_html_template,
            "category": category,
            "variables": variables,
            "is_active": True,
            "description": description,
            "usage_count": 0,
        }
        self._template_repo.insert(doc)

        logger.info("메일 템플릿 생성: %s (변수: %s)", template_id, variables)
        return {"template_id": template_id, "variables": variables}

    def render_template(
        self,
        *,
        template_id: str,
        context: dict[str, str],
    ) -> dict[str, str]:
        """템플릿을 변수로 렌더링한다.

        BR-MAIL-022: 비활성 템플릿은 렌더링 불가.

        EX-MAIL-022: 비활성 템플릿 렌더링 시 에러.
        EX-MAIL-021: 필수 변수 누락 시 에러.
        """
        template = self._template_repo.find_by_id(template_id)
        if not template:
            raise_not_found(f"템플릿 '{template_id}'를 찾을 수 없습니다 [ERR-MAIL-020]")

        # BR-MAIL-022: 비활성 검증
        if not template.get("is_active", True):
            raise_bad_request(
                f"비활성 템플릿 '{template_id}'은(는) 렌더링할 수 없습니다 [ERR-MAIL-022]"
            )

        # EX-MAIL-021: 필수 변수 누락 검증
        required_vars = set(template.get("variables", []))
        provided_vars = set(context.keys())
        missing = required_vars - provided_vars
        if missing:
            raise_bad_request(f"템플릿 변수 누락: {', '.join(sorted(missing))} [ERR-MAIL-021]")

        def _replace(text: str) -> str:
            return _VARIABLE_PATTERN.sub(
                lambda m: context.get(m.group(1), m.group(0)),
                text,
            )

        subject = _replace(template.get("subject_template", ""))
        body = _replace(template.get("body_template", ""))
        body_html = _replace(template.get("body_html_template", ""))

        # 사용 횟수 증가
        self._template_repo.update_by_id(
            template_id,
            {"usage_count": template.get("usage_count", 0) + 1},
        )

        logger.info("메일 템플릿 렌더링: %s", template_id)
        return {"subject": subject, "body": body, "body_html": body_html}
