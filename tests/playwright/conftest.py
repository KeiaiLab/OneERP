"""Playwright 공통 fixture — base_url · fe_url · 브라우저 설정."""

from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="session")
def base_url() -> str:
    """로컬 개발 기본 URL. 실제 실행 시 환경변수 ONEERP_BASE_URL 로 override."""
    return os.environ.get("ONEERP_BASE_URL", "http://localhost:3000")


@pytest.fixture
def fe_url() -> str:
    """Wave D FE 서버 URL. ONEERP_FE_URL 미설정 시 기본값 반환(가드는 skipif 에서 담당)."""
    return os.environ.get("ONEERP_FE_URL", "http://localhost:3000")
