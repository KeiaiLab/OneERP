"""검색 인덱스(SearchIndex) 문서 모델.

포털 통합 검색을 위한 인덱스 엔트리.
BR-PTL-009: 검색 결과 권한 필터링.
BR-PTL-015: 2자 이상 자동완성.
"""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class SearchIndexCreate(BaseModel):
    """검색 인덱스 생성 요청 스키마."""

    doc_type: str = Field(description="문서 유형 (예: sales_order, employee)")
    doc_id: str = Field(description="원본 문서 ID")
    title: str = Field(description="검색 제목")
    content: str = Field(default="", description="검색 내용")
    module: str = Field(default="", description="소속 모듈")
    url: str = Field(default="", description="이동 URL")
    required_permission: str = Field(default="", description="필요 권한")
    keywords: list[str] = Field(default_factory=list, description="검색 키워드")


class SearchIndexUpdate(BaseModel):
    """검색 인덱스 수정 요청 스키마."""

    title: str | None = None
    content: str | None = None
    url: str | None = None
    keywords: list[str] | None = None


class SearchIndex(BaseDocument):
    """검색 인덱스 문서.

    BR-PTL-009: 사용자 권한에 따라 검색 결과를 필터링한다.
    BR-PTL-015: 2자 이상 입력 시 자동완성을 제공한다.
    """

    doc_type: str = ""
    doc_id: str = ""
    title: str = ""
    content: str = ""
    module: str = ""
    url: str = ""
    required_permission: str = ""
    keywords: list[str] = Field(default_factory=list)
