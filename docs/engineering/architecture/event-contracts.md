# 이벤트 contract 규약

## 목적

- 서비스 간 비동기 계약을 `core/oneerp_core/events/schemas.py` 기준으로 고정한다.
- 이벤트 추가/변경/제거 시 CI contract gate가 검출할 수 있는 최소 규칙을 문서화한다.
- producer/consumer가 각자 어떤 하위 호환 책임을 지는지 명시한다.

## canonical envelope

- 모든 이벤트는 `EventEnvelope`로 발행한다.
- 현재 기준 필드는 `event_id`, `event`, `source_service`, `timestamp`, `schema_version` 이다.
- `EventEnvelope.schema_version`의 현재 기본값은 `1`이다.
- `schema_version`은 **envelope + payload 해석 규칙의 메이저 버전**으로 취급한다.

## schema_version 규칙

- 기본 원칙: 같은 `schema_version` 안에서는 backward compatible change만 허용한다.
- 허용:
  - optional 필드 추가
  - consumer가 무시 가능한 메타데이터 추가
  - 기존 의미를 바꾸지 않는 enum/subject 확장
- 금지:
  - 필수 필드 제거
  - 기존 필드의 의미 변경
  - 타입 축소/이름 변경/단위 변경 같은 암묵적 breaking change
- breaking change가 필요하면 다음을 동시에 수행한다.
  1. `schema_version` 증가
  2. migration 계획(expand/migrate/contract) 문서화
  3. producer/consumer 양쪽 검출 게이트 유지

## 이벤트 추가/변경/제거 규칙

### 추가

- 새 이벤트 type 추가는 backward compatible change로 간주한다.
- 새 payload 필드는 optional부터 시작한다.
- consumer는 미인지 이벤트를 무시하거나 dead-letter 처리할 수 있어야 한다.

### 변경

- 같은 `schema_version`에서 payload shape 변경은 additive 방식만 허용한다.
- 기존 consumer가 읽는 필드는 유지한다.
- 의미 변경이 필요한 경우 같은 필드를 재해석하지 말고 새 필드 또는 새 이벤트 type을 만든다.

### 제거

- 이벤트 type 제거는 곧 breaking change다.
- 제거 전 단계에서 producer는 deprecation 기간을 제공해야 한다.
- consumer 제거가 끝나기 전까지 producer는 기존 이벤트 또는 compatibility shim을 유지한다.

## backward compatibility 기본 원칙

- producer는 구 consumer가 깨지지 않도록 additive change만 먼저 배포한다.
- consumer는 자신이 모르는 optional 필드/확장 이벤트를 허용한다.
- event payload는 읽는 쪽보다 쓰는 쪽이 더 엄격해야 한다.
- contract gate는 breaking change를 "허용"할 수는 있어도 "검출 생략"할 수는 없다.

## producer 책임

- `EventEnvelope` 필드를 누락하지 않는다.
- `schema_version`을 명시적으로 유지한다.
- breaking change 전에는 새 필드/새 이벤트를 먼저 확장(expand) 배포한다.
- OpenAPI/API 변경과 함께 이벤트 payload가 달라지는 경우 migration-contracts 문서를 따른다.

## consumer 책임

- `schema_version`을 확인하고 지원 범위를 명시한다.
- unknown optional field를 허용한다.
- 같은 subject 안에서 payload 확장이 와도 안전하게 무시/기본값 처리한다.
- 새 `schema_version` 도입 시 dual-read 또는 compatibility branch를 준비한다.

## contract gate와의 관계

- API contract gate는 `scripts/ci/gen_openapi_types.sh`, `scripts/ci/check_openapi_drift.sh`, `scripts/ci/run_contract_tests.sh`가 담당한다.
- 이벤트 contract는 OpenAPI처럼 자동 추출되지 않으므로, 본 문서를 규칙 SoT로 사용한다.
- breaking change는 API drift, event schema drift, deploy catalog drift를 함께 검토해야 한다.

## Phase 1 NATS 발행·구독 SoT (2026-04-15)

> OPS-04 요건. `core/oneerp_core/events/schemas.py::EventType`이 subject 원천이며,
> 발행은 `oneerp.{event_type.value}` 규칙, 전송은 JetStream 스트림 `ONEERP`
> (subjects=[`oneerp.>`], storage=FILE)를 통한다.

### 공통 envelope / outbox 매핑

- OutboxPoller가 발행하는 payload는 outbox entry 평탄 구조를 그대로 직렬화한다:
  `{event_id, event_type, doc_id, tenant_id, data, triggered_by, published, created_at}`.
- consumer 측 `extract_tenant_and_doc()` 는 봉투(`data.event.*`) 형식과 평탄 형식 양쪽을
  폴백 지원한다(Phase 1 기준 확인 완료).

### Phase 1 범위의 핵심 subject·payload 보강

| subject | producer | 주요 consumer | 핵심 payload(`data.*`) |
|---------|----------|---------------|-------------------------|
| `oneerp.sales_order.submitted` | `sales/selling` | `scm/stock` → 재고 예약 | `doc_id`(=SO ID), `tenant_id` |
| `oneerp.delivery_note.submitted` | `sales/selling` | `scm/stock` → 재고 차감·예약 해제 | `doc_id`(=DN ID), `tenant_id` |
| `oneerp.sales_invoice.submitted` | `sales/selling` | `finance/accounting` → 분개·AR 생성 | `doc_id`, `grand_total`, `net_total`, `customer`, `customer_name`, `posting_date`, `due_date`, `etax_invoice_ref` |
| `oneerp.payment_entry.submitted` | `finance/accounting` | `finance/accounting`(자기소비) → AR/AP 소거 | `doc_id` |
| `oneerp.purchase_receipt.submitted` | `scm/stock` | `scm/stock`(ledger) | `doc_id` |
| `oneerp.purchase_order.submitted` | `scm/buying` | `scm/stock` → 입고 예정 | `doc_id`, `items[]` |
| `oneerp.material.issued` / `oneerp.work_order.completed` | `scm/manufacturing` | `scm/stock` | `work_order_id`, `items[]` 또는 `item_code, produced_qty` |

### 발행 전제 (인프라)

- JetStream 스트림 `ONEERP`가 존재해야 한다. 부재 시 `NatsPublisher.publish`가 silently
  실패해 OutboxPoller→소비자 경로가 끊어진다. 로컬/E2E는 `scripts/dev/init-nats-streams.sh`
  또는 E2E 세션 autouse fixture(`_ensure_nats_stream`)가 보장한다.
- `OutboxPoller`는 각 서비스의 `outbox_collections` 화이트리스트를 세션 시작 시점에
  주입받는다. selling 서비스의 경우 `sales_orders / delivery_notes / sales_invoices /
  quotations`가 기본 대상이다(`services/sales/selling/oneerp_selling_app/main.py`).

### drift 체크

- `scripts/ci/check_event_contract_drift.sh` (Phase 1 스켈레톤): 코드의 subject 선언을
  수집하고 본 문서의 SoT 표와 대조하여 리포트만 출력한다. 완전 자동화는 후속 phase에서
  OpenAPI drift 게이트 수준으로 확장한다.
