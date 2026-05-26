"""POS 서비스 — selling 서비스로 통합됨.

POS 관련 엔티티(pos_transaction, pos_closing_entry 등)는
services/selling/ 에서 구현되어 있다.
이 서비스는 독립 배포 대상이 아니며, 워크스페이스 호환성을 위해 유지한다.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

app = create_service_app(service_name="pos")
