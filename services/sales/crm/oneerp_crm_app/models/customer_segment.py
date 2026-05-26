"""고객 세그먼트(CustomerSegment) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class CustomerSegmentCreate(BaseModel):
    """고객 세그먼트 생성 요청 스키마."""

    segment_name: str
    criteria: str = ""
    customer_count: int = 0
    description: str = ""


class CustomerSegmentUpdate(BaseModel):
    """고객 세그먼트 수정 요청 스키마."""

    segment_name: str | None = None
    criteria: str | None = None
    customer_count: int | None = None
    description: str | None = None


class CustomerSegment(BaseDocument):
    """고객 세그먼트 문서."""

    segment_name: str = ""
    criteria: str = ""
    customer_count: int = 0
    description: str = ""
