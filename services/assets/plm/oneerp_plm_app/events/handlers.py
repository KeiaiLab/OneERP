"""PLM 서비스 이벤트 핸들러.

Manufacturing 서비스의 BOM 관련 이벤트를 수신하여 PLM 데이터를 갱신한다.
"""

from __future__ import annotations

import logging

from oneerp_core.events.handler_registry import EventHandlerRegistry

logger = logging.getLogger(__name__)

event_registry = EventHandlerRegistry()
