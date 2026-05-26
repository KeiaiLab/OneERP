"""사내 메일 커스텀 라우트 -- CRUD 자동 생성 외 추가 엔드포인트."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from oneerp_portal_comms_app.mail.services.mail_folder_service import MailFolderService
from oneerp_portal_comms_app.mail.services.mail_read_service import MailReadService
from oneerp_portal_comms_app.mail.services.mail_send_service import MailSendService
from oneerp_portal_comms_app.mail.services.mail_template_service import MailTemplateService

router = APIRouter(prefix="/api/v1/mail", tags=["사내 메일"])

_DEFAULT_TENANT = "T1"


@router.post("/send", status_code=201)
def send_mail(body: dict[str, Any]) -> dict[str, Any]:
    """메일을 전송한다.

    BR-MAIL-001, BR-MAIL-002, BR-MAIL-005 적용.
    """
    tenant_id = body.pop("tenant_id", _DEFAULT_TENANT)
    svc = MailSendService(tenant_id)
    return svc.send_message(
        sender_id=body.get("sender_id", ""),
        subject=body.get("subject", ""),
        body=body.get("body", ""),
        body_html=body.get("body_html", ""),
        recipients=body.get("recipients", []),
        cc=body.get("cc"),
        bcc=body.get("bcc"),
        priority=body.get("priority", "normal"),
        attachments=body.get("attachments"),
    )


@router.post("/reply", status_code=201)
def reply_mail(body: dict[str, Any]) -> dict[str, Any]:
    """메일에 회신한다.

    BR-MAIL-006 적용.
    """
    tenant_id = body.pop("tenant_id", _DEFAULT_TENANT)
    svc = MailSendService(tenant_id)
    return svc.reply_message(
        original_message_id=body.get("original_message_id", ""),
        sender_id=body.get("sender_id", ""),
        body=body.get("body", ""),
        body_html=body.get("body_html", ""),
        reply_all=body.get("reply_all", False),
    )


@router.post("/forward", status_code=201)
def forward_mail(body: dict[str, Any]) -> dict[str, Any]:
    """메일을 전달한다.

    BR-MAIL-007 적용.
    """
    tenant_id = body.pop("tenant_id", _DEFAULT_TENANT)
    svc = MailSendService(tenant_id)
    return svc.forward_message(
        original_message_id=body.get("original_message_id", ""),
        sender_id=body.get("sender_id", ""),
        forward_to=body.get("forward_to", []),
        body=body.get("body", ""),
        body_html=body.get("body_html", ""),
    )


@router.post("/read/{message_id}")
def read_mail(message_id: str, user_id: str = Query(...)) -> dict[str, Any]:
    """메일을 읽음으로 표시한다.

    BR-MAIL-030, BR-MAIL-032 적용.
    """
    tenant_id = _DEFAULT_TENANT
    svc = MailReadService(tenant_id)
    return svc.read_message(message_id=message_id, user_id=user_id)


@router.post("/unread/{message_id}")
def unread_mail(message_id: str, user_id: str = Query(...)) -> dict[str, Any]:
    """메일을 안읽음으로 표시한다."""
    tenant_id = _DEFAULT_TENANT
    svc = MailReadService(tenant_id)
    return svc.mark_as_unread(message_id=message_id, user_id=user_id)


@router.get("/inbox")
def get_inbox(
    user_id: str = Query(...),
    folder: str = Query("inbox"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> list[dict[str, Any]]:
    """받은편지함 또는 특정 폴더의 메시지를 조회한다."""
    svc = MailReadService(_DEFAULT_TENANT)
    return svc.get_inbox(user_id=user_id, folder=folder, skip=skip, limit=limit)


@router.get("/thread/{thread_id}")
def get_thread(thread_id: str) -> list[dict[str, Any]]:
    """스레드에 속한 모든 메시지를 조회한다."""
    svc = MailReadService(_DEFAULT_TENANT)
    return svc.get_thread(thread_id=thread_id)


@router.get("/search")
def search_mail(
    user_id: str = Query(...),
    q: str = Query(..., min_length=1),
    folder: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> list[dict[str, Any]]:
    """메일을 검색한다.

    BR-MAIL-033 적용.
    """
    svc = MailReadService(_DEFAULT_TENANT)
    return svc.search_messages(user_id=user_id, query=q, folder=folder, limit=limit)


@router.post("/star/{message_id}")
def toggle_star(message_id: str, user_id: str = Query(...)) -> dict[str, Any]:
    """메일 즐겨찾기를 토글한다."""
    svc = MailReadService(_DEFAULT_TENANT)
    return svc.toggle_star(message_id=message_id, user_id=user_id)


@router.delete("/message/{message_id}")
def delete_mail(message_id: str, user_id: str = Query(...)) -> dict[str, Any]:
    """메일을 삭제(소프트)한다.

    BR-MAIL-031 적용.
    """
    svc = MailReadService(_DEFAULT_TENANT)
    return svc.delete_message(message_id=message_id, user_id=user_id)


@router.post("/move")
def move_mail(body: dict[str, Any]) -> dict[str, Any]:
    """메일을 다른 폴더로 이동한다.

    BR-MAIL-013 적용.
    """
    svc = MailFolderService(_DEFAULT_TENANT)
    return svc.move_message(
        user_id=body.get("user_id", ""),
        message_id=body.get("message_id", ""),
        target_folder=body.get("target_folder", "inbox"),
    )


@router.post("/folders/create", status_code=201)
def create_folder(body: dict[str, Any]) -> dict[str, Any]:
    """사용자 폴더를 생성한다.

    BR-MAIL-011, BR-MAIL-012 적용.
    """
    tenant_id = body.pop("tenant_id", _DEFAULT_TENANT)
    svc = MailFolderService(tenant_id)
    return svc.create_folder(
        owner_id=body.get("owner_id", ""),
        name=body.get("name", ""),
        parent_folder_id=body.get("parent_folder_id"),
        color=body.get("color", ""),
        description=body.get("description", ""),
    )


@router.delete("/folders/{folder_id}")
def delete_folder(folder_id: str, owner_id: str = Query(...)) -> dict[str, Any]:
    """사용자 폴더를 삭제한다.

    BR-MAIL-010 적용.
    """
    svc = MailFolderService(_DEFAULT_TENANT)
    return svc.delete_folder(folder_id=folder_id, owner_id=owner_id)


@router.post("/templates/render")
def render_template(body: dict[str, Any]) -> dict[str, str]:
    """메일 템플릿을 렌더링한다.

    BR-MAIL-021, BR-MAIL-022 적용.
    """
    tenant_id = body.pop("tenant_id", _DEFAULT_TENANT)
    svc = MailTemplateService(tenant_id)
    return svc.render_template(
        template_id=body.get("template_id", ""),
        context=body.get("context", {}),
    )


@router.post("/templates/create", status_code=201)
def create_template(body: dict[str, Any]) -> dict[str, Any]:
    """메일 템플릿을 생성한다.

    BR-MAIL-020 적용.
    """
    tenant_id = body.pop("tenant_id", _DEFAULT_TENANT)
    svc = MailTemplateService(tenant_id)
    return svc.create_template(
        template_name=body.get("template_name", ""),
        subject_template=body.get("subject_template", ""),
        body_template=body.get("body_template", ""),
        body_html_template=body.get("body_html_template", ""),
        category=body.get("category", ""),
        description=body.get("description", ""),
    )
