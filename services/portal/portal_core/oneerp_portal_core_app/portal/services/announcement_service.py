"""공지사항 서비스 — 상태 머신, 필수/긴급 공지 관리.

BR-PTL-004: 필수 공지사항 강제 표시.
BR-PTL-005: 선택 공지 '오늘 하루 보지 않기'.
BR-PTL-006: 긴급 공지 빨간 배너.
BR-PTL-011: 동시 긴급 공지 3건 초과 경고.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, cast

from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)

_MAX_URGENT_CONCURRENT = 3

# 상태 전이 규칙: 현재 상태 → 허용되는 다음 상태 목록
_VALID_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["active"],
    "active": ["expired", "archived"],
    "expired": ["archived"],
    "archived": [],
}


class AnnouncementService:
    """공지사항 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._ann_repo = Repository("announcements", tenant_id=tenant_id)
        self._read_repo = Repository("announcement_reads", tenant_id=tenant_id)

    def publish_announcement(
        self, announcement_id: str, *, published_by: str = ""
    ) -> dict[str, Any]:
        """공지사항을 활성화한다 (draft → active).

        BR-PTL-011: 긴급 공지가 3건 초과 시 경고를 포함한다.

        Returns:
            업데이트된 공지사항 dict와 경고 메시지.
        """
        ann = self._get_or_404(announcement_id)
        self._validate_transition(ann, "active")

        # 긴급 공지 동시 활성 건수 확인
        warning = ""
        if ann.get("priority") == "urgent":
            warning = self._check_urgent_limit()

        update_data: dict[str, Any] = {
            "status": "active",
            "published_by": published_by,
        }

        # 시작일이 없으면 현재 시각으로 설정
        if not ann.get("start_date"):
            update_data["start_date"] = datetime.now(tz=UTC)

        self._ann_repo.update_by_id(announcement_id, update_data)

        logger.info(
            "공지사항 활성화: %s (우선순위: %s)",
            announcement_id,
            ann.get("priority", "normal"),
        )
        result = {**ann, **update_data}
        if warning:
            result["_warning"] = warning
        return result

    def expire_announcement(self, announcement_id: str) -> dict[str, Any]:
        """공지사항을 만료 처리한다 (active → expired)."""
        ann = self._get_or_404(announcement_id)
        self._validate_transition(ann, "expired")
        self._ann_repo.update_by_id(announcement_id, {"status": "expired"})
        logger.info("공지사항 만료: %s", announcement_id)
        return {**ann, "status": "expired"}

    def archive_announcement(self, announcement_id: str) -> dict[str, Any]:
        """공지사항을 보관 처리한다 (active/expired → archived)."""
        ann = self._get_or_404(announcement_id)
        self._validate_transition(ann, "archived")
        self._ann_repo.update_by_id(announcement_id, {"status": "archived"})
        logger.info("공지사항 보관: %s", announcement_id)
        return {**ann, "status": "archived"}

    def get_active_announcements(
        self,
        user_id: str,
        *,
        department: str = "",
        role: str = "",
    ) -> list[dict[str, Any]]:
        """사용자에게 표시할 활성 공지사항 목록을 반환한다.

        BR-PTL-004: 필수 공지는 항상 포함.
        BR-PTL-005: '오늘 하루 보지 않기' 반영.
        BR-PTL-006: 긴급 공지를 최상단에 배치.
        """
        now = datetime.now(tz=UTC)

        # 활성 공지 조회
        active = self._ann_repo.find_many({"status": "active"}, limit=100)

        # 날짜 필터
        valid: list[dict[str, Any]] = []
        for ann in active:
            start = ann.get("start_date")
            end = ann.get("end_date")
            if start and start > now:
                continue
            if end and end < now:
                # 자동 만료 처리
                self._ann_repo.update_by_id(ann["_id"], {"status": "expired"})
                continue
            valid.append(ann)

        # 대상 필터 (부서/역할)
        filtered = self._filter_by_target(valid, department=department, role=role)

        # 읽음 상태 반영
        read_records = self._read_repo.find_many({"user_id": user_id}, limit=200)
        hidden_ids = self._get_hidden_announcement_ids(read_records, now)

        # 필수 공지는 hidden 대상에서 제외 (BR-PTL-004)
        result: list[dict[str, Any]] = []
        for ann in filtered:
            ann_id = ann.get("_id", "")
            if ann.get("is_mandatory"):
                result.append({**ann, "_display_mode": "mandatory"})
            elif ann_id not in hidden_ids:
                result.append(ann)

        # 긴급 공지를 최상단으로 (BR-PTL-006)
        result.sort(key=lambda a: 0 if a.get("priority") == "urgent" else 1)

        return result

    def hide_announcement_for_today(
        self,
        announcement_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        """BR-PTL-005: 선택 공지를 오늘 하루 보지 않기 처리한다.

        필수 공지에 대해서는 거부한다 (BR-PTL-004).
        """
        ann = self._get_or_404(announcement_id)

        if ann.get("is_mandatory"):
            raise_bad_request("필수 공지사항은 숨길 수 없습니다 [ERR-PTL-004]")

        now = datetime.now(tz=UTC)
        hide_until = now.replace(hour=23, minute=59, second=59)

        # 기존 읽음 기록 조회
        existing = self._read_repo.find_many(
            {"announcement_id": announcement_id, "user_id": user_id},
            limit=1,
        )

        if existing:
            self._read_repo.update_by_id(
                existing[0]["_id"],
                {"hide_until": hide_until},
            )
        else:
            from oneerp_core.naming import generate_name

            read_id = generate_name("ANNR", tenant_id=self._tenant_id)
            self._read_repo.insert(
                {
                    "_id": read_id,
                    "announcement_id": announcement_id,
                    "user_id": user_id,
                    "read_at": now,
                    "hide_until": hide_until,
                    "tenant_id": self._tenant_id,
                }
            )

        return {"announcement_id": announcement_id, "hidden_until": hide_until.isoformat()}

    def mark_as_read(self, announcement_id: str, user_id: str) -> dict[str, Any]:
        """공지사항을 읽음 처리한다."""
        self._get_or_404(announcement_id)
        now = datetime.now(tz=UTC)

        existing = self._read_repo.find_many(
            {"announcement_id": announcement_id, "user_id": user_id},
            limit=1,
        )

        if not existing:
            from oneerp_core.naming import generate_name

            read_id = generate_name("ANNR", tenant_id=self._tenant_id)
            self._read_repo.insert(
                {
                    "_id": read_id,
                    "announcement_id": announcement_id,
                    "user_id": user_id,
                    "read_at": now,
                    "tenant_id": self._tenant_id,
                }
            )
            # 읽음 수 증가
            self._ann_repo.update_by_id(
                announcement_id,
                {"read_count": (self._get_or_404(announcement_id).get("read_count", 0) + 1)},
            )

        return {"announcement_id": announcement_id, "read_at": now.isoformat()}

    def _check_urgent_limit(self) -> str:
        """BR-PTL-011: 동시 활성 긴급 공지 수를 확인한다."""
        count = self._ann_repo.count({"status": "active", "priority": "urgent"})
        if count >= _MAX_URGENT_CONCURRENT:
            msg = (
                f"동시 활성 긴급 공지가 {count}건입니다. "
                f"최대 {_MAX_URGENT_CONCURRENT}건을 권장합니다 [ERR-PTL-011]"
            )
            logger.warning(msg)
            return msg
        return ""

    def _validate_transition(self, ann: dict[str, Any], target_status: str) -> None:
        """공지사항 상태 전이 유효성을 검증한다.

        Raises:
            OneERPError: 허용되지 않는 상태 전이 시 (ERR-PTL-007).
        """
        current = ann.get("status", "draft")
        allowed = _VALID_TRANSITIONS.get(current, [])
        if target_status not in allowed:
            raise_bad_request(
                f"'{current}' 상태에서 '{target_status}'로 전이할 수 없습니다 [ERR-PTL-007]"
            )

    def _get_or_404(self, announcement_id: str) -> dict[str, Any]:
        """공지사항을 조회하고 없으면 404를 발생시킨다."""
        ann = self._ann_repo.find_by_id(announcement_id)
        if ann is None:
            raise_not_found("공지사항을 찾을 수 없습니다 [ERR-PTL-005]")
        return cast("dict[str, Any]", ann)

    @staticmethod
    def _filter_by_target(
        announcements: list[dict[str, Any]],
        *,
        department: str = "",
        role: str = "",
    ) -> list[dict[str, Any]]:
        """대상 부서/역할로 공지를 필터링한다."""
        result: list[dict[str, Any]] = []
        for ann in announcements:
            target_depts = ann.get("target_departments", [])
            target_roles = ann.get("target_roles", [])

            # 대상이 비어있으면 전체 대상
            if not target_depts and not target_roles:
                result.append(ann)
                continue

            # 부서 매칭
            if target_depts and department and department in target_depts:
                result.append(ann)
                continue

            # 역할 매칭
            if target_roles and role and role in target_roles:
                result.append(ann)
                continue

        return result

    @staticmethod
    def _get_hidden_announcement_ids(
        read_records: list[dict[str, Any]],
        now: datetime,
    ) -> set[str]:
        """숨김 처리된 공지사항 ID 집합을 반환한다."""
        hidden: set[str] = set()
        for record in read_records:
            hide_until = record.get("hide_until")
            if hide_until and hide_until > now:
                hidden.add(record.get("announcement_id", ""))
        return hidden
