"""게시판 관리 서비스 — 게시판 CRUD 및 비즈니스 룰 검증.

BR-BRD-001: 게시판명 테넌트 내 유니크
BR-BRD-013: 게시글이 존재하는 게시판 삭제 불가
"""

from __future__ import annotations

import logging
from typing import Any, cast

from oneerp_core.errors import raise_conflict, raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class BoardService:
    """게시판 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._board_repo = Repository("boards", tenant_id=tenant_id)
        self._post_repo = Repository("posts", tenant_id=tenant_id)
        self._perm_repo = Repository("board_permissions", tenant_id=tenant_id)

    def create_board(self, data: dict[str, Any]) -> dict[str, Any]:
        """게시판을 생성한다.

        BR-BRD-001: 동일 테넌트 내 게시판명 중복 불가.
        """
        board_name = data.get("board_name", "")
        existing = self._board_repo.find_many({"board_name": board_name}, limit=1)
        if existing:
            raise_conflict("ERR-BRD-020: 동일한 이름의 게시판이 이미 존재합니다")

        board_id = generate_name("BRD", tenant_id=self._tenant_id)
        data["_id"] = board_id
        data["tenant_id"] = self._tenant_id
        self._board_repo.insert(data)

        # 기본 권한: 전체 읽기 자동 생성
        perm_id = generate_name("BPM", tenant_id=self._tenant_id)
        self._perm_repo.insert(
            {
                "_id": perm_id,
                "board_id": board_id,
                "grantee_type": "all",
                "grantee_id": None,
                "permission": "read",
                "is_active": True,
                "granted_by": data.get("created_by", ""),
                "tenant_id": self._tenant_id,
            }
        )

        logger.info("게시판 생성: %s (%s)", board_id, board_name)
        return {"_id": board_id, "board_name": board_name}

    def get_board(self, board_id: str) -> dict[str, Any]:
        """게시판 상세를 조회한다."""
        board = self._board_repo.find_by_id(board_id)
        if not board:
            raise_not_found("ERR-BRD-002: 게시판을 찾을 수 없습니다")
        return cast("dict[str, Any]", board)

    def update_board(self, board_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """게시판을 수정한다.

        BR-BRD-001: 이름 변경 시 중복 검사.
        """
        board = self._board_repo.find_by_id(board_id)
        if not board:
            raise_not_found("ERR-BRD-002: 게시판을 찾을 수 없습니다")

        new_name = data.get("board_name")
        if new_name and new_name != board.get("board_name"):
            existing = self._board_repo.find_many({"board_name": new_name}, limit=1)
            if existing:
                raise_conflict("ERR-BRD-020: 동일한 이름의 게시판이 이미 존재합니다")

        self._board_repo.update_by_id(board_id, data)
        logger.info("게시판 수정: %s", board_id)
        return {"_id": board_id, **data}

    def delete_board(self, board_id: str) -> bool:
        """게시판을 삭제한다.

        BR-BRD-013: 게시글이 존재하면 삭제 불가.
        """
        board = self._board_repo.find_by_id(board_id)
        if not board:
            raise_not_found("ERR-BRD-002: 게시판을 찾을 수 없습니다")

        post_count = self._post_repo.count({"board_id": board_id})
        if post_count > 0:
            raise_conflict(
                f"ERR-BRD-037: 게시글이 존재하는 게시판은 삭제할 수 없습니다 ({post_count}건)"
            )

        self._board_repo.delete_by_id(board_id)
        logger.info("게시판 삭제: %s", board_id)
        return True

    def check_board_active(self, board_id: str) -> dict[str, Any]:
        """게시판 활성 상태를 확인한다.

        ERR-BRD-044: 비활성 게시판 접근 차단.
        """
        board = self.get_board(board_id)
        if not board.get("is_active", True):
            raise_unprocessable("ERR-BRD-044", "비활성화된 게시판입니다")
        return board
