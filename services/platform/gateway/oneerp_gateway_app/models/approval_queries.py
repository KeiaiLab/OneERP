"""결재 액션 조회용 쿼리 DTO.

M1-3 도입 목적:
- `routes/approval_actions.py::list_approval_actions()` 가 9개 개별 파라미터
  (user / page / page_size / approval_request / actor / action_type /
  document_type / document_id / from_date / to_date) 로 서명돼 있어 유지보수
  비용이 큼.
- `ApprovalActionListQuery(BaseModel)` 로 묶어 `Depends(ApprovalActionListQuery)`
  패턴으로 라우트 시그니처를 2줄로 축소.
- 동일 쿼리 구조를 사용하는 `report_approval_actions` 등에서도 재사용.

실제 라우트 교체는 M2 selling 파일럿 이후 gateway 마이그레이션 phase 에서.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class ApprovalActionListQuery(BaseModel):
    """결재 액션 목록 조회 필터.

    모든 필드는 선택 — 라우트에서 `Depends(ApprovalActionListQuery)` 로 주입.
    """

    page: int = Field(default=1, ge=1, description="1-based 페이지 번호")
    page_size: int = Field(default=20, ge=1, le=200)

    approval_request: str | None = None
    actor: str | None = None
    action_type: str | None = None

    document_type: str | None = None
    document_id: str | None = None

    from_date: date | None = Field(default=None, description="action_at ≥ from_date")
    to_date: date | None = Field(default=None, description="action_at ≤ to_date")

    def to_mongo_filter(self, tenant_id: str) -> dict[str, object]:
        """FerretDB/MongoDB find 필터 dict 로 변환."""
        filt: dict[str, object] = {"tenant_id": tenant_id}
        if self.approval_request:
            filt["approval_request_id"] = self.approval_request
        if self.actor:
            filt["actor"] = self.actor
        if self.action_type:
            filt["action_type"] = self.action_type
        if self.document_type:
            filt["document_type"] = self.document_type
        if self.document_id:
            filt["document_id"] = self.document_id
        if self.from_date or self.to_date:
            rng: dict[str, object] = {}
            if self.from_date:
                rng["$gte"] = self.from_date.isoformat()
            if self.to_date:
                rng["$lte"] = self.to_date.isoformat()
            filt["action_at"] = rng
        return filt

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.page_size


ApprovalActionListQuery.model_rebuild(_types_namespace={"date": __import__("datetime").date})
