# Observability(초안)

## 범위

- Logging: 구조화 로그(요청 ID/테넌트/유저/리소스)
- Metrics: 핵심 API/작업 큐/DB 지표
- Tracing: 주요 사용자 플로우 end-to-end
- Alerting: SLO 기반 알림

## 책임 구분

- **시스템 로그 구조화**(요청 ID/테넌트/유저/리소스 등 운영 로그): 이 문서가 정의한다.
- **비즈니스 감사 이벤트**(누가/무엇을/왜 변경했는지): `docs/engineering/data/audit-log-spec.md`가 정의한다.

## Phase 0 현황

- **요청 ID 전파**: `RequestIdMiddleware` (`packages/core/oneerp_core/middleware.py`)
  - `X-Request-Id` 헤더로 요청별 추적 ID 부여
  - 클라이언트가 전달하면 그대로 사용, 없으면 UUID 자동 생성
- **구조화 로깅**: Phase 1에서 JSON 로깅 + 중앙 집계 구현 예정

## 확인 필요(Phase 1)

- 기존 스택(Prometheus/Loki/Tempo/Jaeger 등) 유무
- 알림 채널(PagerDuty/Slack 등)
- 구조화된 JSON 로깅 포맷 정의

