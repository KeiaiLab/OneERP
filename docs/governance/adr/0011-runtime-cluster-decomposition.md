# ADR-0011: 코드 조직 — 도메인 클러스터 디렉토리 구조

## 메타데이터

| 필드 | 값 |
|------|----|
| 상태 | Accepted (2026-04-13 채택, 동일자 §0 노트로 범위 축소) |
| 채택일 | 2026-04-13 |
| 결정권자 | OneERP 아키텍처 위원회, 백엔드 리드 |
| 영향 범위 | `services/` 디렉토리 구조, uv workspace 멤버, 코드 import 경계 |
| 관련 ADR | ADR-0014(런타임 plane, **본 ADR과 직교 축**), ADR-0007(라우트), ADR-0008(관측성), ADR-0010(배포) |
| 후속 phase | 진행 중 (`docs/engineering/msa/CONSOLIDATION.md`) |

## 0. 범위 축소 노트 (2026-04-13 동일자)

본 ADR은 채택 당일 작성 직후, **런타임 모델까지 본 ADR 범위에 넣은
잘못된 단언**(이전 초안의 "ADR-0014 supersede")을 발견해 즉시 정정한다.

- OneERP 아키텍처는 **2축 하이브리드**다:
  1. **코드 조직 축** ← **본 ADR**: `services/<cluster>/<domain>/` 디렉토리
     구조와 import 경계.
  2. **런타임 프로세스 축** ← **ADR-0014 (부활, 활성)**: 6개 plane
     (api/realtime/worker/scheduler/edge/extension) 컨테이너 경계.
- 본 ADR은 **축 1만 다룬다.** 컨테이너/프로세스 분할은 ADR-0014가
  단일 진실 출처(SoT — `deploy/catalog/planes.yaml`).
- 따라서 본 ADR은 ADR-0014를 supersede하지 않는다. 두 ADR은 동등하게
  활성이며, 코드(클러스터)와 런타임(plane)이 N:M 관계로 함께 존재한다.

> ADR 불변 원칙의 예외 적용 사유: 채택 당일 동일 위원회 검토에서
> 발견된 사실 오류 정정. 결정 자체의 변경이 아니라 잘못된 단언의 철회.

## 1. 맥락(Context)

OneERP는 출발 시 48개 독립 FastAPI 서비스 + 동일 수의 디렉토리를
가졌다. 도메인 응집도와 무관한 디렉토리 분할은 다음 비용을 만들었다:

- uv workspace 멤버 48개, 동일 마스터(Customer/Item/Supplier/Employee)
  공유 코드의 중복 유지
- import 경로가 `from app.*` 절대 import에 의존, `sys.modules["app"]`
  단일 점유 충돌
- CI matrix 48 잡, RAM 16GB+
- 의미상 같은 도메인의 cross-service HTTP 호출 다수

이는 **코드 조직 문제**이지 런타임 문제는 아니다. 런타임 문제는
ADR-0014가 별도 축으로 해결한다.

근거 인벤토리:
- `docs/engineering/msa/CONSOLIDATION.md`
- `services/` 실제 디렉토리(2026-04-13 측정값: §3 참조)
- `deploy/catalog/services.yaml`(코드 SoT)
- `deploy/catalog/planes.yaml`(런타임 SoT, ADR-0014 관할)

## 2. 결정(Decision)

OneERP의 BE 도메인 코드는 다음 12개 디렉토리 클러스터로 조직한다.
각 클러스터는 도메인 응집도 또는 외부 노출 책임을 공유하는 모듈을
묶는다.

### 2.1 클러스터 12개 (실측 기준, 2026-04-13)

| # | 디렉토리 | 포함 도메인 | 응집 기준 |
|---|---------|-----------|----------|
| 1 | `services/sales/` | selling, crm, pos, commerce(=ecommerce+subscriptions), reservation(=rental+reservation) | Customer 마스터 |
| 2 | `services/scm/` | stock, manufacturing, buying, qm(=maintenance+quality) | Item·BOM·Supplier |
| 3 | `services/finance/` | accounting, expenses, payroll, finance_extra(=consolidation+esg) | GL·차원 |
| 4 | `services/hr/` | hr, learning(=lms+workreport) | Employee 마스터 |
| 5 | `services/collab/` | board, calendar, documents, knowledge, projects, survey, wiki | 협업 |
| 6 | `services/portal/` | portal_comms(=directory+mail), portal_core(=messenger+portal) | 커뮤니케이션 |
| 7 | `services/logistics/` | advanced-planning, logistics(=fleet+tms) | 배송·운송 |
| 8 | `services/marketing/` | gtm, marketing, marketing-automation | 마케팅 스택 |
| 9 | `services/compliance/` | compliance(=clm+compliance_mod) | 법무·계약 |
| 10 | `services/ehs/` | ehs | 안전·보건·환경 |
| 11 | `services/assets/` | assets, plm | 자산·제품수명 |
| 12 | `services/platform/` | gateway, analytics, automation-orchestrator, integration-hub, iot, rpa | 플랫폼·메타 |

추가:
- `services/deploy/` — 배포 산출물 (도메인 코드 X)
- `services/scripts/` — 운영 스크립트
- `services/tests/` — cross-cluster 테스트

### 2.2 보존 원칙
- **라우트 prefix 보존**: `/api/v1/<domain>/*`. ADR-0007 호환.
- **이벤트 체인 보존**: `emit_doc_event → NATS → EventHandlerRegistry`.
- **공통 커널 보존**: `core/oneerp_core/` 무변경.
- **FE 라우트 보존**: `web/app/`의 모든 라우트 그룹.

### 2.3 변경 사항
- uv workspace 멤버는 클러스터 단위(`oneerp-<cluster>`) — 12개
- 클러스터 내부 모듈 import: `oneerp_<cluster>_app.<domain>.<...>` 패턴
- 동일 클러스터 내부 호출: in-process 함수
- 다른 클러스터 호출: HTTP `/api/v1/...` 또는 NATS 이벤트
- 9개 통합 패키지는 2도메인씩 묶어 uv workspace 멤버 수를 제어 (2026-04-13 `_merged` 접미 제거 완료, 통합 설계는 영구)

### 2.4 클러스터 분리 vs 병합 기준
| 조건 | 결정 |
|------|------|
| 공통 마스터 50% 이상 공유 | 병합 |
| 트랜잭션 경계 동일 | 병합 |
| 외부 노출 책임 분리 | 분리 |
| 인프라성 모듈(메타) | platform 클러스터로 통합 |
| 신규 도메인 | 본 표로 분류 후 ADR 갱신 없이 추가 |

### 2.5 클러스터 내부 모듈 경계
- 자체 패키지 디렉토리 (`<cluster>/<domain>/`)
- 다른 모듈 internal API 직접 호출 금지 (선언된 인터페이스만)
- 공유 코드는 `<cluster>/_shared/` 또는 `core/oneerp_core/`
- 정적 분석: import linter로 강제

### 2.6 런타임과의 관계 (ADR-0014 보강)
- 본 ADR이 정의한 12개 코드 클러스터는 런타임 시 6개 plane으로 재조립
- 매핑: 한 도메인 모듈은 책임에 따라 1개 이상의 plane에서 호스팅
  - 예: `services/finance/accounting/` 내 HTTP 라우트 → `api_plane`
  - 예: 동일 코드의 워커 잡 → `worker_plane`
  - 예: 스케줄된 마감 → `scheduler_plane`
- 매핑 SoT: `deploy/catalog/planes.yaml` (ADR-0014)

- **범위 In**: `services/`, `core/`, uv workspace 정의, import 경계.
- **범위 Out**:
  - 런타임 컨테이너 분할 (ADR-0014)
  - FE 디렉토리 (`web/`)
  - 인프라 매니페스트

## 3. 실측 데이터 (2026-04-13)

```text
services/
├── sales/           5 도메인
├── scm/             4 도메인
├── finance/         4 도메인
├── hr/              2 도메인
├── collab/          7 도메인
├── portal/          2 도메인 (portal_comms + portal_core, 각 2 하위 도메인 통합)
├── logistics/       2 도메인
├── marketing/       3 도메인
├── compliance/      1 도메인 (clm + compliance_mod 통합)
├── ehs/             1 도메인
├── assets/          2 도메인
├── platform/        6 도메인 (gateway 포함)
├── deploy/          (배포 산출물)
├── scripts/         (운영)
└── tests/           (cross-cluster)
```

총: **12 도메인 클러스터 + 39 도메인 모듈**.

(ADR-0012의 47 모듈은 ERD 인덱스 기준이며, 2도메인 통합 패키지로 일부
모듈이 단일 디렉토리에 합쳐진 상태다. ADR-0012 매핑은 ERD 단위 그대로
유지되고, 본 ADR은 디렉토리 단위만 정의한다.)

## 4. 대안(Alternatives Considered)

### 대안 A — 48 디렉토리 유지
- 단점: 운영·CI·자원 부담.
- 채택하지 않은 이유: 측정 데이터로 명확.

### 대안 B — 19 클러스터(이전 캠페인 목표)
- 단점: 일부 클러스터(commerce/procurement/learning)는 단독 의미가
  약해 sales/scm/hr/finance에 흡수되는 게 자연스러움. 19를 강제하면
  인위적 분리.
- 채택하지 않은 이유: 실측 데이터가 12 분류로 수렴.

### 대안 C — DDD Bounded Context (예: 7~10개)
- 단점: 일부 도메인의 분기점 모호, 임의 결정 빈발.
- 채택하지 않은 이유: §2.4 명시 기준이 더 객관.

### 대안 D — 단일 모놀리식 디렉토리
- 단점: 팀 소유권·배포 빈도·변경 영향 격리 손실.
- 채택하지 않은 이유: 클러스터 단위 격리 가치.

## 5. 근거(Rationale)

| 평가 축 | 점수 | 비고 |
|---------|------|------|
| 비용 | 5/5 | 12 디렉토리는 측정값과 자연 일치 |
| 리스크 | 4/5 | import linter + 라우트/이벤트 보존으로 BC 100% |
| 운영 | 5/5 | 클러스터 단위 owner·CI 단순 |
| 팀 역량 | 5/5 | 도메인 응집은 친숙 |

## 6. 영향(Consequences)

### 6.1 긍정적
- 코드 위치를 클러스터 단위로 단순 결정.
- 클러스터 단위 owner·CI 매트릭스 가능.
- 런타임(plane)과 직교라 양 축을 독립 진화 가능.

### 6.2 부정적
- 9개 통합 패키지(commerce·reservation·qm·finance_extra·learning·compliance·portal_comms·portal_core·logistics)는 2도메인씩 영구 통합 설계.
- 런타임/코드 2축 동시 이해 부담 → §2.6과 ADR-0014 §매핑 표로 완화.

### 6.3 호환성/마이그레이션
- 라우트·이벤트 보존으로 외부 BC 영향 0.
- 2026-04-13 `_merged` 접미 제거 완료. 통합 설계 자체는 유지.

### 6.4 측정 지표

| 지표 | 현재(2026-04-13) | 목표(6개월) |
|------|------------------|-------------|
| 디렉토리 클러스터 수 | 12 | 12 (안정) |
| `_merged` 접미 디렉토리 | 0 | 0 (2026-04-13 제거 완료) |
| import linter 위반 | 측정 시작 | 0 |
| cross-cluster HTTP URL | 측정 | < 10 |
| uv workspace 멤버 | 측정 | 12 |

## 7. 실행 항목

- [x] 백엔드 — `_merged` 접미 제거 (2026-04-13, 9 디렉토리 + 9 패키지 + services.yaml + 2 plane main.py + 6 Helm chart + 107 Python import)
- [ ] 플랫폼 — 클러스터 import linter 룰 — 2026-06-15
- [ ] 인프라 — uv workspace 12 멤버 통합 — 캠페인 P5
- [ ] 인프라 — 클러스터↔plane 매핑 표 발행 (ADR-0014 부록 갱신) — 2026-05-15

## 8. 검증

- [ ] CI에 import linter 활성
- [ ] 분기 cross-cluster HTTP URL 카운트 측정
- [ ] `services/` 디렉토리 트리와 본 ADR §2.1·§3 일치 자동 점검

## 9. 부록 — ADR-0014와의 매핑

본 ADR(코드)와 ADR-0014(런타임)의 N:M 매핑 예:

| 코드 클러스터 | 주 plane | 보조 plane |
|--------------|----------|-----------|
| platform/gateway | edge | api |
| platform/integration-hub | extension | worker |
| platform/automation-orchestrator | scheduler | worker |
| platform/analytics | api | worker |
| platform/iot | extension | realtime |
| platform/rpa | worker | scheduler |
| sales/* | api | worker (이메일·집계) |
| scm/* | api | worker (재고 재계산), scheduler (마감) |
| finance/* | api | scheduler (마감), worker (보고) |
| hr/* | api | scheduler (급여), worker (알림) |
| collab/* | api | realtime (알림), worker |
| portal/* | api | realtime (메시지) |
| logistics/* | api | scheduler |
| marketing/* | api | worker |
| compliance/* | api | worker |
| ehs/* | api | scheduler |
| assets/* | api | scheduler (점검) |

자세한 매핑은 `deploy/catalog/planes.yaml` 참조.

## 10. 참고 자료

- `docs/engineering/msa/CONSOLIDATION.md`
- `deploy/catalog/services.yaml` (코드 SoT)
- `deploy/catalog/planes.yaml` (런타임 SoT — ADR-0014)
- ADR-0014 (런타임 plane), ADR-0007 (라우트), ADR-0008 (관측성), ADR-0010 (배포)
- Sam Newman — Building Microservices (2nd Ed.)
