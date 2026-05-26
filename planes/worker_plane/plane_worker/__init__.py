"""OneERP Worker Plane (P3, ADR-0014).

outbox poller + event consumer. 58 EventType 핸들러를 전 도메인에서 수집하여
단일 프로세스에서 구독. 무상태, scale-to-zero 가능.

M2 TODO: 각 도메인 oneerp_{svc}_app.events.event_registry 를 임포트하여
NATS JetStream 에 일괄 등록. 현 시점은 스캐폴드만.
"""
