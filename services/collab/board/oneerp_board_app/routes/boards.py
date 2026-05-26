"""게시판 커스텀 라우트 — EntityMeta CRUD 외 비즈니스 엔드포인트.

L2-spec 5.1, 5.2 API 계약에 따른 추가 엔드포인트.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["게시판"])


@router.delete("/boards/{board_id}/with-validation")
async def delete_board_with_validation(board_id: str) -> dict[str, str]:
    """게시판 삭제 (게시글 존재 시 차단).

    BR-BRD-013: 게시글이 존재하는 게시판 삭제 불가.
    기본 CRUD DELETE는 이 검증을 수행하지 않으므로 별도 엔드포인트 제공.
    """
    from oneerp_board_app.services.board_service import BoardService

    svc = BoardService("T1")
    svc.delete_board(board_id)
    return {"status": "deleted", "board_id": board_id}
