"""Mail 서비스 엔티티 메타 선언 -- CRUD 라우터 자동 생성용.

6개 엔티티를 EntityMeta로 선언한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.mail_auto_rule import (
    MailAutoRule,
    MailAutoRuleCreate,
    MailAutoRuleUpdate,
)
from .models.mail_distribution_list import (
    MailDistributionList,
    MailDistributionListCreate,
    MailDistributionListUpdate,
)
from .models.mail_folder import (
    MailFolder,
    MailFolderCreate,
    MailFolderUpdate,
)
from .models.mail_message import (
    MailMessage,
    MailMessageCreate,
    MailMessageUpdate,
)
from .models.mail_recipient_status import (
    MailRecipientStatus,
    MailRecipientStatusCreate,
    MailRecipientStatusUpdate,
)
from .models.mail_template import (
    MailTemplate,
    MailTemplateCreate,
    MailTemplateUpdate,
)

# --- 마스터 데이터 ---

MAIL_FOLDER = EntityMeta(
    collection="mail_folders",
    prefix="MFLD",
    api_path="/api/v1/mail-folders",
    tag="메일 폴더",
    resource="mail_folder",
    model=MailFolder,
    create_schema=MailFolderCreate,
    update_schema=MailFolderUpdate,
    archetype="master",
    not_found_message="메일 폴더를 찾을 수 없습니다",
)

MAIL_TEMPLATE = EntityMeta(
    collection="mail_templates",
    prefix="MTPL",
    api_path="/api/v1/mail-templates",
    tag="메일 템플릿",
    resource="mail_template",
    model=MailTemplate,
    create_schema=MailTemplateCreate,
    update_schema=MailTemplateUpdate,
    archetype="master",
    not_found_message="메일 템플릿을 찾을 수 없습니다",
)

MAIL_DISTRIBUTION_LIST = EntityMeta(
    collection="mail_distribution_lists",
    prefix="MDLS",
    api_path="/api/v1/mail-distribution-lists",
    tag="메일 배포 목록",
    resource="mail_distribution_list",
    model=MailDistributionList,
    create_schema=MailDistributionListCreate,
    update_schema=MailDistributionListUpdate,
    archetype="master",
    not_found_message="메일 배포 목록을 찾을 수 없습니다",
)

MAIL_AUTO_RULE = EntityMeta(
    collection="mail_auto_rules",
    prefix="MARL",
    api_path="/api/v1/mail-auto-rules",
    tag="메일 자동 분류 규칙",
    resource="mail_auto_rule",
    model=MailAutoRule,
    create_schema=MailAutoRuleCreate,
    update_schema=MailAutoRuleUpdate,
    archetype="master",
    not_found_message="메일 자동 분류 규칙을 찾을 수 없습니다",
)

# --- 트랜잭션 문서 ---

MAIL_MESSAGE = EntityMeta(
    collection="mail_messages",
    prefix="MAIL",
    api_path="/api/v1/mail-messages",
    tag="메일 메시지",
    resource="mail_message",
    model=MailMessage,
    create_schema=MailMessageCreate,
    update_schema=MailMessageUpdate,
    archetype="transaction",
    not_found_message="메일 메시지를 찾을 수 없습니다",
)

MAIL_RECIPIENT_STATUS = EntityMeta(
    collection="mail_recipient_statuses",
    prefix="MRST",
    api_path="/api/v1/mail-recipient-statuses",
    tag="수신자 메일 상태",
    resource="mail_recipient_status",
    model=MailRecipientStatus,
    create_schema=MailRecipientStatusCreate,
    update_schema=MailRecipientStatusUpdate,
    archetype="transaction",
    not_found_message="수신자 메일 상태를 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    MAIL_FOLDER,
    MAIL_TEMPLATE,
    MAIL_DISTRIBUTION_LIST,
    MAIL_AUTO_RULE,
    # 트랜잭션
    MAIL_MESSAGE,
    MAIL_RECIPIENT_STATUS,
]
