"""투표 서비스 — 투표 생성, 투표하기, 결과 조회 비즈니스 로직.

SC-SVY-006: 실시간 투표.
SC-SVY-010: 비밀 투표 (익명).
EX-SVY-005: 중복 투표 거부.
EX-SVY-010: 마감된 투표 거부.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast

from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class PollService:
    """투표 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._poll_repo = Repository("polls", tenant_id=tenant_id)
        self._vote_repo = Repository("poll_votes", tenant_id=tenant_id)

    def cast_vote(self, poll_id: str, vote_data: dict[str, Any]) -> dict[str, Any]:
        """투표를 수행한다.

        ERR-SVY-070: 중복 투표 거부.
        ERR-SVY-071: 마감된 투표 거부.
        """
        poll = self._get_poll_or_404(poll_id)

        # 마감 상태 확인
        if poll.get("status") == "closed":
            raise_unprocessable("ERR-SVY-071", "마감된 투표입니다")

        # 중복 투표 확인
        voter_hash = vote_data.get("voter_hash")
        voter_id = vote_data.get("voter_id")

        if voter_hash:
            existing = self._vote_repo.find_many(
                {"poll_id": poll_id, "voter_hash": voter_hash}, limit=1
            )
            if existing:
                raise_unprocessable("ERR-SVY-070", "이미 투표했습니다")

        if voter_id:
            existing = self._vote_repo.find_many(
                {"poll_id": poll_id, "voter_id": voter_id}, limit=1
            )
            if existing:
                raise_unprocessable("ERR-SVY-070", "이미 투표했습니다")

        # 익명 투표면 voter_id 제거
        if poll.get("anonymity") == "anonymous":
            vote_data["voter_id"] = None

        # 투표 기록 생성
        vote_id = generate_name("PV", tenant_id=self._tenant_id)
        doc = {
            "_id": vote_id,
            "poll_id": poll_id,
            **vote_data,
            "voted_at": datetime.now(tz=UTC),
            "tenant_id": self._tenant_id,
        }
        self._vote_repo.insert(doc)

        # 선택지별 vote_count 증가 + total_votes 증가
        selected = vote_data.get("selected_options", [])
        options = poll.get("options", [])
        updated_options = []
        for opt in options:
            new_opt = dict(opt)
            if new_opt.get("option_id") in selected:
                new_opt["vote_count"] = new_opt.get("vote_count", 0) + 1
            updated_options.append(new_opt)

        total_votes = poll.get("total_votes", 0) + 1
        self._poll_repo.update_by_id(
            poll_id, {"options": updated_options, "total_votes": total_votes}
        )

        logger.info("투표 완료: %s → %s", vote_id, poll_id)
        return doc

    def get_results(self, poll_id: str) -> dict[str, Any]:
        """투표 결과를 반환한다 (비율 포함)."""
        poll = self._get_poll_or_404(poll_id)

        total = poll.get("total_votes", 0)
        options = poll.get("options", [])

        results: list[dict[str, Any]] = []
        for opt in options:
            count = opt.get("vote_count", 0)
            percentage = Decimal(str(round(count / total * 100, 1))) if total > 0 else Decimal(0)
            results.append(
                {
                    "option_id": opt.get("option_id"),
                    "text": opt.get("text"),
                    "vote_count": count,
                    "percentage": percentage,
                }
            )

        return {
            "poll_id": poll_id,
            "title": poll.get("title"),
            "total_votes": total,
            "options": results,
        }

    def close_poll(self, poll_id: str) -> dict[str, Any]:
        """투표를 마감한다."""
        poll = self._get_poll_or_404(poll_id)
        if poll.get("status") == "closed":
            raise_unprocessable("ERR-SVY-071", "이미 마감된 투표입니다")

        self._poll_repo.update_by_id(poll_id, {"status": "closed"})
        logger.info("투표 마감: %s", poll_id)
        return {**poll, "status": "closed"}

    def _get_poll_or_404(self, poll_id: str) -> dict[str, Any]:
        """투표를 조회하고 없으면 404를 발생시킨다."""
        poll = self._poll_repo.find_by_id(poll_id)
        if poll is None:
            raise_not_found("투표를 찾을 수 없습니다")
        return cast("dict[str, Any]", poll)
