"""Playwright E2E 공통 헬퍼 — 재사용 가능한 UI 동작."""

from __future__ import annotations

from playwright.sync_api import Page, expect


def login(
    page: Page,
    base_url: str,
    username: str = "demo",
    password: str = "demo1234",  # noqa: S107
) -> None:
    """로그인 수행."""
    page.goto(f"{base_url}/login")
    page.fill("#username", username)
    page.fill("#password", password)
    page.click('button[type="submit"]')
    page.wait_for_url(f"{base_url}/", timeout=10000)


def navigate_to_entity(page: Page, base_url: str, entity: str) -> None:
    """사이드바에서 엔티티 페이지로 이동한다."""
    page.goto(f"{base_url}/{entity}")
    page.wait_for_load_state("networkidle")


def create_entity(page: Page, base_url: str, entity: str, fields: dict) -> str:
    """엔티티 생성 페이지에서 필드를 입력하고 저장한다."""
    page.goto(f"{base_url}/{entity}/new")
    page.wait_for_load_state("networkidle")

    for key, value in fields.items():
        field = page.locator(f'[name="{key}"]')
        if field.count() > 0:
            field.fill(str(value))

    page.click('button:has-text("저장")')
    page.wait_for_url(f"**/{entity}/**", timeout=10000)
    return page.url.split("/")[-1]  # 생성된 ID 반환


def submit_document(page: Page) -> None:
    """현재 문서를 제출(Submit)한다."""
    page.click('button:has-text("제출")')
    # 확인 다이얼로그가 있으면 확인 클릭
    confirm = page.locator('button:has-text("확인")')
    if confirm.count() > 0:
        confirm.click()
    page.wait_for_load_state("networkidle")


def wait_for_toast(page: Page, text: str = "", timeout: int = 5000) -> None:
    """토스트 메시지가 나타날 때까지 대기한다."""
    page.locator('[role="alert"]').wait_for(timeout=timeout)
    if text:
        expect(page.locator('[role="alert"]')).to_contain_text(text)


def get_table_row_count(page: Page) -> int:
    """목록 테이블의 행 수를 반환한다."""
    return page.locator("tbody tr").count()


def click_table_row(page: Page, index: int = 0) -> None:
    """목록 테이블의 N번째 행을 클릭한다."""
    page.locator("tbody tr").nth(index).click()
    page.wait_for_load_state("networkidle")
