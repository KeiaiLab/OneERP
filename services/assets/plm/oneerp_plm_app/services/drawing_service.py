"""도면 서비스 — 체크아웃/체크인, 리비전 관리 비즈니스 로직."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from oneerp_core.errors import raise_bad_request, raise_conflict, raise_forbidden, raise_not_found
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


def _next_revision(current: str) -> str:
    """다음 리비전 문자를 반환한다.

    A → B → ... → Z → AA → AB → ...
    """
    if len(current) == 1 and current < "Z":
        return chr(ord(current) + 1)
    if current == "Z":
        return "AA"
    # 다중 문자 리비전
    last = current[-1]
    if last < "Z":
        return current[:-1] + chr(ord(last) + 1)
    return current + "A"


class DrawingService:
    """도면 관리 비즈니스 로직.

    체크아웃/체크인으로 동시 편집을 방지하고 리비전을 관리한다.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._drawing_repo = Repository("drawings", tenant_id=tenant_id)

    def checkout(self, drawing_id: str, user_id: str) -> dict[str, Any]:
        """도면을 체크아웃한다 (잠금).

        Args:
            drawing_id: 도면 ID
            user_id: 체크아웃 사용자 ID

        Returns:
            체크아웃 결과
        """
        drawing = self._drawing_repo.find_by_id(drawing_id)
        if not drawing:
            raise_not_found(f"도면을 찾을 수 없습니다: {drawing_id}")

        if drawing.get("status") == "obsolete":
            raise_bad_request("폐기된 도면은 체크아웃할 수 없습니다")

        checked_out_by = drawing.get("checked_out_by")
        if checked_out_by:
            raise_conflict(f"도면이 이미 체크아웃 상태입니다. 체크아웃 사용자: {checked_out_by}")

        now = datetime.now(tz=UTC)
        self._drawing_repo.update_by_id(
            drawing_id,
            {
                "checked_out_by": user_id,
                "checked_out_at": now.isoformat(),
            },
        )

        logger.info("도면 체크아웃: drawing=%s, user=%s", drawing_id, user_id)
        return {"drawing_id": drawing_id, "checked_out_by": user_id}

    def checkin(
        self,
        drawing_id: str,
        user_id: str,
        file_url: str,
        file_name: str,
        file_size: int,
        change_summary: str = "",
    ) -> dict[str, Any]:
        """도면을 체크인한다 (새 리비전 업로드).

        Args:
            drawing_id: 도면 ID
            user_id: 체크인 사용자 ID
            file_url: 새 파일 URL
            file_name: 새 파일명
            file_size: 새 파일 크기
            change_summary: 변경 요약

        Returns:
            체크인 결과
        """
        drawing = self._drawing_repo.find_by_id(drawing_id)
        if not drawing:
            raise_not_found(f"도면을 찾을 수 없습니다: {drawing_id}")

        checked_out_by = drawing.get("checked_out_by")
        if not checked_out_by:
            raise_bad_request("체크아웃 상태가 아닌 도면은 체크인할 수 없습니다")

        if checked_out_by != user_id:
            raise_forbidden(
                f"체크아웃한 사용자만 체크인할 수 있습니다. 체크아웃 사용자: {checked_out_by}"
            )

        current_revision = drawing.get("revision", "A")
        new_revision = _next_revision(current_revision)

        # 리비전 이력에 이전 리비전 추가
        revision_history = drawing.get("revision_history", [])
        revision_history.append(
            {
                "revision": new_revision,
                "file_url": file_url,
                "change_summary": change_summary,
                "released_by": user_id,
                "released_at": datetime.now(tz=UTC).isoformat(),
            }
        )

        self._drawing_repo.update_by_id(
            drawing_id,
            {
                "revision": new_revision,
                "file_url": file_url,
                "file_name": file_name,
                "file_size": file_size,
                "revision_history": revision_history,
                "checked_out_by": None,
                "checked_out_at": None,
                "updated_by": user_id,
            },
        )

        logger.info(
            "도면 체크인: drawing=%s, revision=%s → %s",
            drawing_id,
            current_revision,
            new_revision,
        )
        return {
            "drawing_id": drawing_id,
            "previous_revision": current_revision,
            "new_revision": new_revision,
        }

    def release(self, drawing_id: str, user_id: str) -> dict[str, Any]:
        """도면을 릴리즈한다.

        Args:
            drawing_id: 도면 ID
            user_id: 릴리즈 승인자 ID

        Returns:
            릴리즈 결과
        """
        drawing = self._drawing_repo.find_by_id(drawing_id)
        if not drawing:
            raise_not_found(f"도면을 찾을 수 없습니다: {drawing_id}")

        if drawing.get("checked_out_by"):
            raise_bad_request("체크아웃 상태의 도면은 릴리즈할 수 없습니다")

        if drawing.get("status") == "obsolete":
            raise_bad_request("폐기된 도면은 릴리즈할 수 없습니다")

        self._drawing_repo.update_by_id(
            drawing_id,
            {
                "status": "released",
                "updated_by": user_id,
            },
        )

        logger.info("도면 릴리즈: drawing=%s", drawing_id)
        return {"drawing_id": drawing_id, "status": "released"}
