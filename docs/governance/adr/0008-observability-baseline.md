# ADR-0008: 관측성 baseline (metric · log · trace · audit)

## 메타데이터

| 필드 | 값 |
|------|----|
| 상태 | Accepted |
| 채택일 | 2026-04-13 |
| 결정권자 | OneERP 아키텍처 위원회, SRE 리드 |
| 영향 범위 | 모든 BE 서비스, 백그라운드 작업, FE 핵심 페이지 |
| 관련 ADR | ADR-0001(G4-1), ADR-0006(권한 감사), ADR-0009(백업), ADR-0011(plane) |
| 후속 phase | P-012 (관측성 코어), P-013 (대시보드·알림) |

## 1. 맥락(Context)

ADR-0001 G4-1은 "표준 메트릭, 구조화 로그, OpenTelemetry trace,
`/healthz`·`/readyz` 정상" 4가지를 모듈 상용화 게이트로 명시한다.
SLO(`docs/infra/ops/slo.md`)는 가용성·지연·에러율 측정을 전제한다.
현재(`docs/infra/ops/observability.md`):

- `RequestIdMiddleware`만 존재 (Phase 0)
- 구조화 로깅 미구현
- 메트릭 노출 미구현
- trace 미구현
- 알림·대시보드 미구성

이 상태에서 SLO를 측정·집행할 수 없다. 또한 **모듈마다 다른 로그
포맷·메트릭 이름**을 쓰면 cross-module 분석·인시던트 대응이 불가능
하다. 통일 baseline이 필요하다.

근거 인벤토리:
- `docs/infra/ops/observability.md`
- `docs/infra/ops/slo.md`
- `docs/engineering/data/audit-log-spec.md`
- `packages/core/oneerp_core/middleware.py` (`RequestIdMiddleware`)
- OpenTelemetry semantic conventions

## 2. 결정(Decision)

OneERP는 **OpenTelemetry(OTel) 단일 표준 + Prometheus 메트릭 + 구조화
JSON 로그 + 별도 감사 채널**의 4축 baseline을 채택한다.

### 2.1 4축 책임 분리
| 축 | 무엇 | 어디로 | 보존 |
|----|------|--------|------|
| Metric | 수치(요청수·지연·에러율·큐깊이·DB지연) | Prometheus | 13개월 |
| Log | 시스템 이벤트(요청·예외·결정) | Loki(JSON) | 30일(hot)+1년(cold) |
| Trace | 분산 호출 그래프 | Tempo (OTLP) | 14일 |
| Audit | 비즈니스 행위(누가/무엇을) | FerretDB `audit_events` + 영구 보관 | 7년 |

### 2.2 의무 항목 (모든 서비스·모든 모듈)

#### Health
- `GET /healthz` — 프로세스 살아있음 (캐시 가능)
- `GET /readyz` — 의존성(DB, IdP, NATS) 준비 완료
- `GET /metrics` — Prometheus 포맷

#### Metric (의무 시리즈)
- `http_requests_total{method,route,status,tenant_class}`
- `http_request_duration_seconds{method,route,le}` (히스토그램)
- `http_request_errors_total{method,route,error_code}`
- `db_query_duration_seconds{collection,op,le}`
- `task_queue_depth{queue}`
- `task_duration_seconds{task,outcome,le}`
- `tenant_active{tenant_class}` (gauge)
- `auth_decisions_total{decision,reason}`

라벨 카디널리티 가드: `tenant_id` 자체는 라벨 X (tenant_class만). 필요한
경우 별도 exemplar.

#### Log (구조화 JSON 표준 필드)
```json
{
  "ts": "2026-04-13T12:34:56.789Z",
  "level": "INFO",
  "service": "selling",
  "module": "selling",
  "version": "1.4.2",
  "request_id": "uuid",
  "trace_id": "otlp-trace-id",
  "span_id": "otlp-span-id",
  "tenant_id": "tnt_xxx",
  "user_id": "usr_xxx",
  "route": "/api/v1/sales/invoices",
  "method": "POST",
  "status": 201,
  "duration_ms": 42,
  "msg": "invoice created",
  "extra": { ... }
}
```
- 자유 텍스트 금지(stack trace 제외)
- 필드명 snake_case
- 시크릿/PII 자동 마스킹 (`***` + 해시)
- `print()` 절대 금지 (전역 규칙 + ruff T20)

#### Trace
- 모든 HTTP 요청 자동 instrument (FastAPI middleware)
- DB 쿼리, 외부 호출, 큐 작업 자동 span
- 비즈니스 임계 작업은 수동 span (예: 회계 마감)
- Sampling: 기본 10%, 에러는 100%, 핵심 비즈니스 작업 100%
- W3C `traceparent` 헤더 전파 (cross-plane)

#### Audit (ADR-0006 보강)
- 모든 `submit/approve/cancel/amend/export/share/delete` + 권한 Deny
- 스키마: `docs/engineering/data/audit-log-spec.md` 준수
- 변경 내용 diff 포함 (필드 단위)
- 7년 보존, 변조 방지(append-only + checksum chain)

### 2.3 네이밍 규칙
- 메트릭: OpenMetrics + OTel semantic conventions 준수
- 로그 필드: snake_case
- 큐: `oneerp.<plane>.<module>.<purpose>` (예: `oneerp.api.selling.email`)
- 토픽(NATS): `oneerp.events.<module>.<event_v{N}>` (이벤트 버전 포함)

### 2.4 알림 라우팅
ADR-0001 SLO 알림 규칙(`docs/infra/ops/slo.md` §알림 규칙) 준수.
- Critical → PagerDuty + Slack `#ops-critical`
- Warning → Slack `#ops-warning` (집계, 1시간)
- 모듈별 채널은 모듈 README에 명시

- **범위 In**: 모든 서비스, 모든 모듈, 모든 환경(dev/stg/prod).
- **범위 Out**:
  - APM 상용 도구(별도 ADR로 검토)
  - 비즈니스 분석/BI(별도 ADR)
  - 클라이언트(브라우저) RUM (별도 ADR)

## 3. 대안(Alternatives Considered)

### 대안 A — 상용 APM 단일(Datadog/NewRelic)
- 장점: 단일 SaaS, 빠른 설정.
- 단점: 비용, 데이터 외부 유출, 멀티테넌시 격리 복잡.
- 채택하지 않은 이유: 데이터 주권, 비용. 향후 옵션으로 별도 ADR.

### 대안 B — 자체 ELK + Statsd
- 단점: OTel 표준 외, 도구별 학습 비용 누적.
- 채택하지 않은 이유: OTel 통일 가치 손실.

### 대안 C — 메트릭만, 로그/트레이스 생략
- 단점: 인시던트 대응 불가.
- 채택하지 않은 이유: G4-1 미달.

### 대안 D — 현 상태 유지
- 채택하지 않은 이유: SLO 측정 불가.

## 4. 근거(Rationale)

| 평가 축 | 점수 | 비고 |
|---------|------|------|
| 비용 | 4/5 | OSS 스택, 자체 호스팅 |
| 리스크 | 5/5 | SLO 집행 + 인시던트 진단 가능 |
| 운영 | 4/5 | 4축 책임 분리로 부담 분산 |
| 팀 역량 | 3/5 | OTel 학습 곡선 → 템플릿/SDK로 완화 |

## 5. 영향(Consequences)

### 5.1 긍정적
- SLO 측정·알림 가능.
- 인시던트 평균 진단 시간 단축.
- 모듈 간 로그/메트릭 호환.

### 5.2 부정적
- 인프라(Prometheus/Loki/Tempo) 운영 부담.
- 고카디널리티 라벨 사용 금지로 일부 분석 제한 → exemplar로 보완.

### 5.3 호환성
- 기존 `RequestIdMiddleware` 유지, OTel 미들웨어와 협력.

### 5.4 측정 지표

| 지표 | 현재 | 목표(6개월) |
|------|------|-------------|
| `/metrics` 노출 서비스 | 0 | 100% |
| 구조화 로그 적용율 | 0% | 100% |
| Trace 발신 라우트 | 0% | 100% |
| 알림 false-positive율 | n/a | < 5% |
| 인시던트 평균 진단 | n/a | < 30분 |

## 6. SDK 표준 (packages/core 제공)

```python
# packages/core/oneerp_core/observability.py (예정)
from oneerp_core.observability import logger, meter, tracer, audit

logger.info("invoice_created", extra={"invoice_id": ...})
meter.counter("oneerp.invoice.created", 1, attrs={...})
with tracer.span("invoice.compute_total") as span: ...
audit.emit(action="submit", entity="SalesInvoice", record_id=...)
```

FE는 `@oneerp/observability` 패키지로 동등 인터페이스 제공.

## 7. 환경별 차이

| 환경 | Sampling | 보존 | 알림 |
|------|----------|------|------|
| dev | 100% | 7일 | 콘솔만 |
| stg | 50% | 14일 | Slack `#stg-ops` |
| prod | 10%(에러 100%) | 표준 | PagerDuty + Slack |

## 8. 실행 항목

- [ ] SRE — Prometheus/Loki/Tempo 클러스터 구축 — 2026-05-15 — phase: P-012
- [ ] 코어팀 — `oneerp_core/observability` SDK — 2026-05-15
- [ ] 코어팀 — FastAPI OTel 미들웨어 + healthz/readyz/metrics — 2026-05-31
- [ ] FE팀 — `@oneerp/observability` SDK — 2026-06-15
- [ ] SRE — SLO 대시보드 + 알림 룰 — 2026-06-30 — phase: P-013
- [ ] 모든 모듈 오너 — 의무 메트릭/로그/trace 적용 — Wave 진입 시

## 9. 검증

- [ ] CI에 `/healthz`, `/readyz`, `/metrics` smoke 테스트
- [ ] 라벨 카디널리티 검사 (Prometheus admission)
- [ ] 분기 알림 감사(false positive율 점검)

## 10. 부록 A — 라벨 카디널리티 규칙

| 라벨 | 허용 카디널리티 | 비고 |
|------|----------------|------|
| `route` | < 200 | 동적 ID는 placeholder로 정규화 |
| `tenant_class` | 5 미만 | tier1/tier2/tier3 + system + unknown |
| `error_code` | < 100 | 표준 카탈로그 |
| `tenant_id` | 사용 금지 | exemplar로 |

## 11. 부록 B — 인시던트 진단 흐름 표준

```text
알림 수신
  │
  ▼
SLO 대시보드 (어느 SLI?)
  │
  ▼
모듈/라우트 메트릭 (지연·에러율)
  │
  ▼
구조화 로그 검색 (request_id로)
  │
  ▼
Trace 조회 (trace_id로)
  │
  ▼
Audit 조회 (변경 행위가 있었는가)
  │
  ▼
근본 원인 → INC 작성 → 회귀 테스트
```

## 12. 참고 자료

- `docs/infra/ops/observability.md`
- `docs/infra/ops/slo.md`
- `docs/engineering/data/audit-log-spec.md`
- OpenTelemetry: <https://opentelemetry.io>
- Prometheus naming: <https://prometheus.io/docs/practices/naming/>
- Google SRE Book — Monitoring Distributed Systems
- ADR-0001 G4-1, ADR-0006
