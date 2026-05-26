"""뉴스레터(Newsletter) 문서 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class NewsletterCreate(BaseModel):
    """뉴스레터 생성 요청 스키마."""

    newsletter_name: str
    subject: str = ""
    content: str = ""
    send_date: date | None = None
    subscriber_count: int = 0


class NewsletterUpdate(BaseModel):
    """뉴스레터 수정 요청 스키마."""

    newsletter_name: str | None = None
    subject: str | None = None
    content: str | None = None
    send_date: date | None = None
    subscriber_count: int | None = None


class Newsletter(BaseDocument):
    """뉴스레터 문서."""

    newsletter_name: str = ""
    subject: str = ""
    content: str = ""
    send_date: date | None = None
    subscriber_count: int = 0
