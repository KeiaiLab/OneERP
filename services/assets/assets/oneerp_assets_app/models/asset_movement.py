"""자산이동(AssetMovement) 문서 모델 — Assets 모듈."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class AssetMovementCreate(BaseModel):
    """자산이동 생성 요청 스키마."""

    asset: str
    asset_name: str = ""
    from_location: str = ""
    to_location: str = ""
    movement_date: date | None = None
    purpose: str = "transfer"


class AssetMovementUpdate(BaseModel):
    """자산이동 수정 요청 스키마."""

    asset: str | None = None
    asset_name: str | None = None
    from_location: str | None = None
    to_location: str | None = None
    movement_date: date | None = None
    purpose: str | None = None


class AssetMovement(BaseDocument):
    """자산이동 문서 — Assets 자산이동 트랜잭션.

    naming prefix: AMOV
    """

    asset: str = ""
    asset_name: str = ""
    from_location: str = ""
    to_location: str = ""
    movement_date: date | None = None
    purpose: str = "transfer"
