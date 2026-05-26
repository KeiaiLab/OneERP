"""포털 커스텀 라우터 — 레이아웃, 바로가기, 공지, 검색, 위젯, 뉴스 API.

18+ 엔드포인트를 제공한다. ERR-PTL-* 에러 코드 참조.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from oneerp_core.deps import CurrentUserDep
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository
from oneerp_core.route_helpers import get_or_404, paginated_list

from ..services.announcement_service import AnnouncementService
from ..services.news_service import NewsService
from ..services.portal_layout_service import PortalLayoutService
from ..services.search_service import SearchService
from ..services.shortcut_service import ShortcutService
from ..services.widget_service import WidgetService

router = APIRouter(prefix="/api/v1/portal", tags=["사내 포털"])


def _user_role(user: CurrentUserDep, override: str = "") -> str:
    return override or user.user_tier


def _user_permissions(user: CurrentUserDep) -> list[str]:
    return list(user.permissions)


# ──────────────────────────────────────────────
# 사용자 엔드포인트 — 레이아웃
# ──────────────────────────────────────────────


@router.get("/me/layout")
def get_my_layout(
    user: CurrentUserDep,
    department: str = "",
    role: str = "",
) -> dict[str, Any]:
    """현재 사용자의 최종 레이아웃을 반환한다 (BR-PTL-001 상속 해석)."""
    svc = PortalLayoutService(user.tenant_id)
    return svc.resolve_user_layout(
        user.sub,
        department=department,
        role=_user_role(user, role),
    )


# ──────────────────────────────────────────────
# 사용자 엔드포인트 — 바로가기
# ──────────────────────────────────────────────


@router.get("/me/shortcuts")
def get_my_shortcuts(user: CurrentUserDep) -> list[dict[str, Any]]:
    """내 바로가기 목록을 조회한다."""
    svc = ShortcutService(user.tenant_id)
    return svc.get_user_shortcuts(user.sub)


@router.post("/me/shortcuts", status_code=201)
def create_my_shortcut(
    user: CurrentUserDep,
    shortcut_name: str = Query(description="바로가기 이름"),
    url: str = Query(description="대상 URL"),
    icon: str = Query(default="link"),
    color: str = Query(default="#1976D2"),
    sort_order: int = Query(default=0),
) -> dict[str, Any]:
    """바로가기를 생성한다 (BR-PTL-003: 최대 20개)."""
    svc = ShortcutService(user.tenant_id)
    return svc.create_shortcut(
        user_id=user.sub,
        shortcut_name=shortcut_name,
        url=url,
        icon=icon,
        color=color,
        sort_order=sort_order,
    )


@router.post("/me/shortcuts/{shortcut_id}/click")
def track_shortcut_click(
    shortcut_id: str,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """바로가기 클릭을 추적한다."""
    svc = ShortcutService(user.tenant_id)
    return svc.track_click(shortcut_id, user.sub)


@router.delete("/me/shortcuts/{shortcut_id}", status_code=204)
def delete_my_shortcut(shortcut_id: str, user: CurrentUserDep) -> None:
    """바로가기를 삭제한다."""
    svc = ShortcutService(user.tenant_id)
    svc.delete_shortcut(shortcut_id, user.sub)


# ──────────────────────────────────────────────
# 사용자 엔드포인트 — 공지사항
# ──────────────────────────────────────────────


@router.get("/me/announcements")
def get_my_announcements(
    user: CurrentUserDep,
    department: str = "",
    role: str = "",
) -> list[dict[str, Any]]:
    """사용자에게 표시할 활성 공지사항을 반환한다."""
    svc = AnnouncementService(user.tenant_id)
    return svc.get_active_announcements(
        user.sub,
        department=department,
        role=_user_role(user, role),
    )


@router.post("/me/announcements/{announcement_id}/read")
def mark_announcement_read(
    announcement_id: str,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """공지사항을 읽음 처리한다."""
    svc = AnnouncementService(user.tenant_id)
    return svc.mark_as_read(announcement_id, user.sub)


@router.post("/me/announcements/{announcement_id}/hide")
def hide_announcement_today(
    announcement_id: str,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """공지사항을 오늘 하루 보지 않기 (BR-PTL-005)."""
    svc = AnnouncementService(user.tenant_id)
    return svc.hide_announcement_for_today(announcement_id, user.sub)


# ──────────────────────────────────────────────
# 사용자 엔드포인트 — 검색
# ──────────────────────────────────────────────


@router.get("/search")
def search_portal(
    user: CurrentUserDep,
    q: str = Query(description="검색어"),
    module: str = Query(default="", description="모듈 필터"),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[dict[str, Any]]:
    """통합 검색을 수행한다 (BR-PTL-009 권한 필터링)."""
    svc = SearchService(user.tenant_id)
    permissions = _user_permissions(user)
    return svc.search(q, user_permissions=permissions, module=module, limit=limit)


@router.get("/search/autocomplete")
def autocomplete(
    user: CurrentUserDep,
    q: str = Query(description="입력 문자열"),
) -> list[dict[str, Any]]:
    """자동완성을 수행한다 (BR-PTL-015: 2자 이상)."""
    svc = SearchService(user.tenant_id)
    permissions = _user_permissions(user)
    return svc.autocomplete(q, user_permissions=permissions)


# ──────────────────────────────────────────────
# 사용자 엔드포인트 — 위젯
# ──────────────────────────────────────────────


@router.get("/me/widgets")
def get_my_widgets(
    user: CurrentUserDep,
    role: str = "",
) -> list[dict[str, Any]]:
    """사용자에게 사용 가능한 위젯 목록을 반환한다."""
    svc = WidgetService(user.tenant_id)
    permissions = _user_permissions(user)
    return svc.get_available_widgets(
        user_permissions=permissions,
        user_role=_user_role(user, role),
    )


@router.get("/widgets/{widget_id}/data")
def get_widget_data(
    widget_id: str,
    user: CurrentUserDep,
    role: str = "",
) -> dict[str, Any]:
    """위젯 데이터를 조회한다 (BR-PTL-014 역할별 스코프)."""
    svc = WidgetService(user.tenant_id)
    return svc.get_widget_data(widget_id, user_role=_user_role(user, role))


# ──────────────────────────────────────────────
# 사용자 엔드포인트 — 뉴스/이벤트
# ──────────────────────────────────────────────


@router.get("/news")
def list_news(
    user: CurrentUserDep,
    department: str = "",
    event_type: str = "",
    limit: int = Query(default=20, ge=1, le=100),
) -> list[dict[str, Any]]:
    """게시된 뉴스/이벤트 목록을 반환한다."""
    svc = NewsService(user.tenant_id)
    return svc.get_published_news(
        department=department,
        event_type=event_type,
        limit=limit,
    )


@router.post("/news/{news_id}/view")
def view_news(news_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """뉴스/이벤트 조회 수를 증가시킨다."""
    svc = NewsService(user.tenant_id)
    return svc.increment_view_count(news_id)


# ──────────────────────────────────────────────
# 관리자 엔드포인트 — 레이아웃 CRUD
# ──────────────────────────────────────────────


@router.post(
    "/admin/layouts",
    status_code=201,
    dependencies=[Depends(require_permission("portal_layout:create"))],
)
def create_layout(
    body: dict[str, Any],
    user: CurrentUserDep,
) -> dict[str, Any]:
    """관리자 레이아웃을 생성한다."""
    from ..models.portal_layout import PortalLayoutCreate

    validated = PortalLayoutCreate(**body)
    repo = Repository("portal_layouts", tenant_id=user.tenant_id)
    layout_id = generate_name("PTLL", tenant_id=user.tenant_id)
    doc = {
        "_id": layout_id,
        **validated.model_dump(),
        "tenant_id": user.tenant_id,
        "created_by": user.sub,
        "updated_by": user.sub,
    }
    repo.insert(doc)
    return doc


@router.get(
    "/admin/layouts",
    dependencies=[Depends(require_permission("portal_layout:read"))],
)
def list_layouts(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """관리자 레이아웃 목록을 조회한다."""
    repo = Repository("portal_layouts", tenant_id=user.tenant_id)
    return paginated_list(repo, page, page_size)


@router.get(
    "/admin/layouts/{layout_id}",
    dependencies=[Depends(require_permission("portal_layout:read"))],
)
def get_layout(layout_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """레이아웃 상세를 조회한다."""
    repo = Repository("portal_layouts", tenant_id=user.tenant_id)
    return get_or_404(repo, layout_id, "포털 레이아웃을 찾을 수 없습니다 [ERR-PTL-001]")


@router.put(
    "/admin/layouts/{layout_id}",
    dependencies=[Depends(require_permission("portal_layout:write"))],
)
def update_layout(
    layout_id: str,
    body: dict[str, Any],
    user: CurrentUserDep,
) -> dict[str, Any]:
    """레이아웃을 수정한다 (BR-PTL-010 잠금 확인)."""
    svc = PortalLayoutService(user.tenant_id)
    layout = svc.get_layout_or_404(layout_id)
    svc.check_layout_lock(layout)

    if "widgets" in body:
        svc.validate_widget_count(body["widgets"])

    repo = Repository("portal_layouts", tenant_id=user.tenant_id)
    repo.update_by_id(layout_id, {**body, "updated_by": user.sub})
    return {**layout, **body}


@router.delete(
    "/admin/layouts/{layout_id}",
    status_code=204,
    dependencies=[Depends(require_permission("portal_layout:delete"))],
)
def delete_layout(layout_id: str, user: CurrentUserDep) -> None:
    """레이아웃을 삭제한다."""
    repo = Repository("portal_layouts", tenant_id=user.tenant_id)
    get_or_404(repo, layout_id, "포털 레이아웃을 찾을 수 없습니다 [ERR-PTL-001]")
    repo.delete_by_id(layout_id)


# ──────────────────────────────────────────────
# 관리자 엔드포인트 — 공지사항 CRUD
# ──────────────────────────────────────────────


@router.post(
    "/admin/announcements",
    status_code=201,
    dependencies=[Depends(require_permission("announcement:create"))],
)
def create_announcement(
    body: dict[str, Any],
    user: CurrentUserDep,
) -> dict[str, Any]:
    """공지사항을 생성한다."""
    from ..models.announcement import AnnouncementCreate

    validated = AnnouncementCreate(**body)
    repo = Repository("announcements", tenant_id=user.tenant_id)
    ann_id = generate_name("ANN", tenant_id=user.tenant_id)
    doc = {
        "_id": ann_id,
        **validated.model_dump(),
        "status": "draft",
        "read_count": 0,
        "tenant_id": user.tenant_id,
        "created_by": user.sub,
        "updated_by": user.sub,
    }
    repo.insert(doc)
    return doc


@router.post(
    "/admin/announcements/{announcement_id}/publish",
    dependencies=[Depends(require_permission("announcement:write"))],
)
def publish_announcement(
    announcement_id: str,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """공지사항을 활성화한다 (draft → active)."""
    svc = AnnouncementService(user.tenant_id)
    return svc.publish_announcement(announcement_id, published_by=user.sub)


@router.post(
    "/admin/announcements/{announcement_id}/expire",
    dependencies=[Depends(require_permission("announcement:write"))],
)
def expire_announcement(
    announcement_id: str,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """공지사항을 만료 처리한다."""
    svc = AnnouncementService(user.tenant_id)
    return svc.expire_announcement(announcement_id)


@router.post(
    "/admin/announcements/{announcement_id}/archive",
    dependencies=[Depends(require_permission("announcement:write"))],
)
def archive_announcement(
    announcement_id: str,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """공지사항을 보관 처리한다."""
    svc = AnnouncementService(user.tenant_id)
    return svc.archive_announcement(announcement_id)


# ──────────────────────────────────────────────
# 관리자 엔드포인트 — 뉴스/이벤트 CRUD
# ──────────────────────────────────────────────


@router.post(
    "/admin/news",
    status_code=201,
    dependencies=[Depends(require_permission("news_event:create"))],
)
def create_news(
    body: dict[str, Any],
    user: CurrentUserDep,
) -> dict[str, Any]:
    """뉴스/이벤트를 생성한다."""
    from ..models.news_event import NewsEventCreate

    validated = NewsEventCreate(**body)
    repo = Repository("news_events", tenant_id=user.tenant_id)
    news_id = generate_name("NEWS", tenant_id=user.tenant_id)
    doc = {
        "_id": news_id,
        **validated.model_dump(),
        "status": "draft",
        "view_count": 0,
        "tenant_id": user.tenant_id,
        "created_by": user.sub,
        "updated_by": user.sub,
    }
    repo.insert(doc)
    return doc


@router.post(
    "/admin/news/{news_id}/publish",
    dependencies=[Depends(require_permission("news_event:write"))],
)
def publish_news(
    news_id: str,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """뉴스/이벤트를 게시한다."""
    svc = NewsService(user.tenant_id)
    return svc.publish(news_id, published_by=user.sub)


@router.post(
    "/admin/news/{news_id}/archive",
    dependencies=[Depends(require_permission("news_event:write"))],
)
def archive_news(
    news_id: str,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """뉴스/이벤트를 보관 처리한다."""
    svc = NewsService(user.tenant_id)
    return svc.archive(news_id)
