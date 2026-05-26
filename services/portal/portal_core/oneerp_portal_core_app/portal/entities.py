"""Portal 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

9개 엔티티를 EntityMeta로 선언한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.announcement import Announcement, AnnouncementCreate, AnnouncementUpdate
from .models.announcement_read import (
    AnnouncementRead,
    AnnouncementReadCreate,
    AnnouncementReadUpdate,
)
from .models.news_event import NewsEvent, NewsEventCreate, NewsEventUpdate
from .models.personal_dashboard import (
    PersonalDashboard,
    PersonalDashboardCreate,
    PersonalDashboardUpdate,
)
from .models.portal_layout import PortalLayout, PortalLayoutCreate, PortalLayoutUpdate
from .models.search_index import SearchIndex, SearchIndexCreate, SearchIndexUpdate
from .models.shortcut import Shortcut, ShortcutCreate, ShortcutUpdate
from .models.widget import Widget, WidgetCreate, WidgetUpdate
from .models.widget_config import WidgetConfig, WidgetConfigCreate, WidgetConfigUpdate

# --- 마스터 데이터 ---

PORTAL_LAYOUT = EntityMeta(
    collection="portal_layouts",
    prefix="PTLL",
    api_path="/api/v1/portal-layouts",
    tag="포털 레이아웃",
    resource="portal_layout",
    model=PortalLayout,
    create_schema=PortalLayoutCreate,
    update_schema=PortalLayoutUpdate,
    archetype="master",
    not_found_message="포털 레이아웃을 찾을 수 없습니다",
)

WIDGET = EntityMeta(
    collection="widgets",
    prefix="WGT",
    api_path="/api/v1/widgets",
    tag="위젯",
    resource="widget",
    model=Widget,
    create_schema=WidgetCreate,
    update_schema=WidgetUpdate,
    archetype="master",
    not_found_message="위젯을 찾을 수 없습니다",
)

# --- 트랜잭션 문서 ---

WIDGET_CONFIG = EntityMeta(
    collection="widget_configs",
    prefix="WGTC",
    api_path="/api/v1/widget-configs",
    tag="위젯 설정",
    resource="widget_config",
    model=WidgetConfig,
    create_schema=WidgetConfigCreate,
    update_schema=WidgetConfigUpdate,
    archetype="transaction",
    not_found_message="위젯 설정을 찾을 수 없습니다",
)

SHORTCUT = EntityMeta(
    collection="shortcuts",
    prefix="SCUT",
    api_path="/api/v1/shortcuts",
    tag="바로가기",
    resource="shortcut",
    model=Shortcut,
    create_schema=ShortcutCreate,
    update_schema=ShortcutUpdate,
    archetype="transaction",
    not_found_message="바로가기를 찾을 수 없습니다",
)

ANNOUNCEMENT = EntityMeta(
    collection="announcements",
    prefix="ANN",
    api_path="/api/v1/announcements",
    tag="공지사항",
    resource="announcement",
    model=Announcement,
    create_schema=AnnouncementCreate,
    update_schema=AnnouncementUpdate,
    archetype="transaction",
    not_found_message="공지사항을 찾을 수 없습니다",
)

ANNOUNCEMENT_READ = EntityMeta(
    collection="announcement_reads",
    prefix="ANNR",
    api_path="/api/v1/announcement-reads",
    tag="공지사항 읽음",
    resource="announcement_read",
    model=AnnouncementRead,
    create_schema=AnnouncementReadCreate,
    update_schema=AnnouncementReadUpdate,
    archetype="transaction",
    not_found_message="공지사항 읽음 기록을 찾을 수 없습니다",
)

PERSONAL_DASHBOARD = EntityMeta(
    collection="personal_dashboards",
    prefix="PDASH",
    api_path="/api/v1/personal-dashboards",
    tag="개인 대시보드",
    resource="personal_dashboard",
    model=PersonalDashboard,
    create_schema=PersonalDashboardCreate,
    update_schema=PersonalDashboardUpdate,
    archetype="transaction",
    not_found_message="개인 대시보드를 찾을 수 없습니다",
)

SEARCH_INDEX = EntityMeta(
    collection="search_indices",
    prefix="SIDX",
    api_path="/api/v1/search-indices",
    tag="검색 인덱스",
    resource="search_index",
    model=SearchIndex,
    create_schema=SearchIndexCreate,
    update_schema=SearchIndexUpdate,
    archetype="transaction",
    not_found_message="검색 인덱스를 찾을 수 없습니다",
)

NEWS_EVENT = EntityMeta(
    collection="news_events",
    prefix="NEWS",
    api_path="/api/v1/news-events",
    tag="뉴스/이벤트",
    resource="news_event",
    model=NewsEvent,
    create_schema=NewsEventCreate,
    update_schema=NewsEventUpdate,
    archetype="transaction",
    not_found_message="뉴스/이벤트를 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    PORTAL_LAYOUT,
    WIDGET,
    # 트랜잭션
    WIDGET_CONFIG,
    SHORTCUT,
    ANNOUNCEMENT,
    ANNOUNCEMENT_READ,
    PERSONAL_DASHBOARD,
    SEARCH_INDEX,
    NEWS_EVENT,
]
