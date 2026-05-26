"""메신저 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

6개 엔티티를 EntityMeta로 선언한다.
채널, 메시지는 커스텀 로직이 있어 routes/에서 직접 관리하며,
나머지 엔티티는 EntityMeta 기반 CRUD를 사용한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.bookmark import Bookmark, BookmarkCreate, BookmarkUpdate
from .models.notification import Notification, NotificationCreate, NotificationUpdate
from .models.thread import Thread, ThreadCreate, ThreadUpdate
from .models.user_presence import UserPresence, UserPresenceCreate, UserPresenceUpdate

# --- 마스터 데이터 ---

USER_PRESENCE = EntityMeta(
    collection="user_presences",
    prefix="PRS",
    api_path="/api/v1/user-presences",
    tag="사용자프레즌스",
    resource="user_presence",
    model=UserPresence,
    create_schema=UserPresenceCreate,
    update_schema=UserPresenceUpdate,
    archetype="master",
    not_found_message="사용자 프레즌스를 찾을 수 없습니다",
)

# --- 트랜잭션 문서 ---

NOTIFICATION = EntityMeta(
    collection="notifications",
    prefix="NTF",
    api_path="/api/v1/notifications",
    tag="알림",
    resource="notification",
    model=Notification,
    create_schema=NotificationCreate,
    update_schema=NotificationUpdate,
    archetype="transaction",
    not_found_message="알림을 찾을 수 없습니다",
)

THREAD = EntityMeta(
    collection="threads",
    prefix="THR",
    api_path="/api/v1/threads",
    tag="스레드",
    resource="thread",
    model=Thread,
    create_schema=ThreadCreate,
    update_schema=ThreadUpdate,
    archetype="transaction",
    not_found_message="스레드를 찾을 수 없습니다",
)

BOOKMARK = EntityMeta(
    collection="bookmarks",
    prefix="BKM",
    api_path="/api/v1/bookmarks",
    tag="북마크",
    resource="bookmark",
    model=Bookmark,
    create_schema=BookmarkCreate,
    update_schema=BookmarkUpdate,
    archetype="transaction",
    not_found_message="북마크를 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    USER_PRESENCE,
    # 트랜잭션
    NOTIFICATION,
    THREAD,
    BOOKMARK,
]
