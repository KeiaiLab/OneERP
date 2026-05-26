"""메일 폴더 서비스 -- 폴더 관리 비즈니스 로직.

BR-MAIL-010: 기본 폴더(inbox, sent, drafts, trash)는 삭제 불가.
BR-MAIL-011: 폴더명은 같은 사용자 내에서 중복될 수 없다.
BR-MAIL-012: 폴더 계층은 최대 3단계까지 허용한다.
BR-MAIL-013: 메일 이동 시 폴더 카운터를 갱신한다.
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.errors import raise_bad_request, raise_conflict, raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_portal_comms_app.mail.models.mail_folder import SYSTEM_FOLDERS

logger = logging.getLogger(__name__)


class MailFolderService:
    """메일 폴더 비즈니스 로직.

    SC-MAIL-010: 사용자 폴더 생성 정상 시나리오
    SC-MAIL-011: 폴더간 메일 이동 정상 시나리오
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._folder_repo = Repository("mail_folders", tenant_id=tenant_id)
        self._recipient_repo = Repository("mail_recipient_statuses", tenant_id=tenant_id)

    def create_folder(
        self,
        *,
        owner_id: str,
        name: str,
        parent_folder_id: str | None = None,
        color: str = "",
        description: str = "",
    ) -> dict[str, Any]:
        """사용자 폴더를 생성한다.

        BR-MAIL-011: 폴더명 중복 검증.
        BR-MAIL-012: 폴더 계층 깊이 제한.

        EX-MAIL-011: 폴더명 중복 시 에러.
        EX-MAIL-012: 3단계 초과 시 에러.
        """
        # BR-MAIL-011: 폴더명 중복 검증
        existing = self._folder_repo.find_many(
            {"owner_id": owner_id, "name": name},
            limit=1,
        )
        if existing:
            raise_conflict(f"폴더명 '{name}'이(가) 이미 존재합니다 [ERR-MAIL-011]")

        # BR-MAIL-012: 폴더 계층 깊이 계산
        depth = 0
        if parent_folder_id:
            parent = self._folder_repo.find_by_id(parent_folder_id)
            if not parent:
                raise_not_found(f"상위 폴더 '{parent_folder_id}'를 찾을 수 없습니다 [ERR-MAIL-012]")
            depth = parent.get("depth", 0) + 1
            max_depth = 3
            if depth > max_depth:
                raise_bad_request(f"폴더 계층은 최대 {max_depth}단계까지 허용됩니다 [ERR-MAIL-012]")

        folder_id = generate_name("MFLD", tenant_id=self._tenant_id)
        doc = {
            "_id": folder_id,
            "name": name,
            "owner_id": owner_id,
            "parent_folder_id": parent_folder_id,
            "color": color,
            "description": description,
            "depth": depth,
            "is_system": False,
            "message_count": 0,
            "unread_count": 0,
        }
        self._folder_repo.insert(doc)

        logger.info("메일 폴더 생성: %s (소유자: %s)", folder_id, owner_id)
        return {"folder_id": folder_id, "name": name, "depth": depth}

    def delete_folder(self, *, folder_id: str, owner_id: str) -> dict[str, Any]:
        """사용자 폴더를 삭제한다.

        BR-MAIL-010: 시스템 폴더는 삭제 불가.

        EX-MAIL-010: 시스템 폴더 삭제 시도 시 에러.
        """
        folder = self._folder_repo.find_by_id(folder_id)
        if not folder:
            raise_not_found(f"폴더 '{folder_id}'를 찾을 수 없습니다 [ERR-MAIL-010]")

        if folder.get("is_system") or folder.get("name", "").lower() in SYSTEM_FOLDERS:
            raise_bad_request(
                "시스템 폴더(inbox, sent, drafts, trash)는 삭제할 수 없습니다 [ERR-MAIL-010]"
            )

        if folder.get("owner_id") != owner_id:
            raise_bad_request("본인 소유의 폴더만 삭제할 수 있습니다 [ERR-MAIL-010]")

        self._folder_repo.delete_by_id(folder_id)

        logger.info("메일 폴더 삭제: %s (소유자: %s)", folder_id, owner_id)
        return {"folder_id": folder_id, "deleted": True}

    def move_message(
        self,
        *,
        user_id: str,
        message_id: str,
        target_folder: str,
    ) -> dict[str, Any]:
        """메일을 다른 폴더로 이동한다.

        BR-MAIL-013: 폴더 카운터를 갱신한다.
        """
        statuses = self._recipient_repo.find_many(
            {"message_id": message_id, "user_id": user_id},
            limit=1,
        )
        if not statuses:
            raise_not_found(f"메시지 '{message_id}'의 수신 상태를 찾을 수 없습니다 [ERR-MAIL-013]")

        status = statuses[0]
        old_folder = status.get("folder", "inbox")
        self._recipient_repo.update_by_id(
            status["_id"],
            {"folder": target_folder},
        )

        logger.info(
            "메일 이동: %s → %s (사용자: %s)",
            old_folder,
            target_folder,
            user_id,
        )
        return {
            "message_id": message_id,
            "from_folder": old_folder,
            "to_folder": target_folder,
        }

    def get_user_folders(self, *, owner_id: str) -> list[dict[str, Any]]:
        """사용자의 폴더 목록을 반환한다."""
        return self._folder_repo.find_many(
            {"owner_id": owner_id},
            limit=100,
        )
