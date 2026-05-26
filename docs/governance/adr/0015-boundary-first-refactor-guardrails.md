# ADR-0015: 경계 우선 대규모 리팩토링 가드레일

## 메타데이터

| 필드 | 값 |
|------|----|
| 상태 | Accepted |
| 채택일 | 2026-04-14 |
| 결정권자 | OneERP 아키텍처 위원회 |
| 영향 범위 | `services/`, `planes/`, `web/`, `deploy/catalog/`, `docs/` |
| 관련 ADR | ADR-0011(코드 클러스터), ADR-0014(런타임 plane), ADR-0003(테스트 게이트), ADR-0007(API 계약) |
| 후속 phase | 해당 없음 |

## 1. 맥락(Context)

Task 1 실측은 대규모 리팩토링의 기준선이 문서 서술이 아니라 코드/스크립트 사실이어야 함을 보여줬다.

- 백엔드 shared kernel 결합 축은 `oneerp_core.document(693)`, `oneerp_core.repository(309)`, `oneerp_core.naming(212)` 이 가장 강했다.
- route→repository 위반은 `Repository(...)` 직접 인스턴스화 184건, `oneerp_core.repository` 직접 import 114건이었다.
- FE 계약은 `EntityConfig` 기반 service mapping 375개가 중심이고, generated OpenAPI type files는 2개뿐이었다.
- `web/lib/crud/api-client.ts` 경로의 generic CRUD 외 직접 `apiFetch` 우회 화면은 4개였다.
- `deploy/catalog/services.yaml` 실측 key는 43개였고 문서 숫자와 불일치했다.
- `deploy/catalog/planes.yaml`에는 문서가 말한 `includes:` 가 없었다.

이 상태에서 리팩토링을 코드로 먼저 밀어붙이면 경계가 더 흐려질 수 있으므로, 먼저 목표 구조와 가드레일을 고정한다.

## 2. 결정(Decision)

OneERP는 도메인 중심 코드 클러스터 + 6 Runtime Plane + thin shared kernel 의 하이브리드 구조로 고정하고, shared kernel·plane·FE·deploy/docs 경계를 가드레일로 선행 고정한다.

### 2.1 범위 In
- `services/` 도메인 코드 조직
- `planes/` 런타임 조립 경계
- `web/` 계약/registry 경계
- `deploy/catalog/` 렌더링 기준선
- `docs/`와 `.sisyphus/`의 의사결정/기록 정합성

### 2.2 범위 Out
- 제품 코드 수정
- 테스트/CI 워크플로우 수정
- deploy manifest 수정
- ADR 본문을 통한 기존 결정의 소급 변경

### 2.3 목표 구조
- 코드 조직은 도메인 중심으로 유지한다.
- 런타임은 api/realtime/worker/scheduler/edge/extension 6 plane 으로 유지한다.
- shared kernel 은 얇게 유지한다.
- plane 은 조립 전용이고, 도메인 규칙은 가지지 않는다.
- web 은 registry와 API 계약의 소비자다.
- deploy/catalog 은 렌더링 기준선이고, prose 설명보다 실측 key 집합이 우선한다.

### 2.4 shared kernel 허용/금지 책임

**허용 책임**
- 인증/테넌트/에러/요청 추적 같은 횡단 관심사
- DB/세션/부트스트랩 같은 실행 공통 인프라
- 순수한 문서/이름/이벤트 형식 공통화
- 여러 도메인이 공유하는 타입/인터페이스

**금지 책임**
- 도메인 비즈니스 규칙
- route 전용 persistence 결합
- 서비스별 enum/상수/이름표
- 도메인 workflow, 권한 정책, CRUD 정책
- plane 마운트/라우팅 결정

즉, `repository`, `document`, `naming`, `app_factory`, `testing` 은 공통화 대상이 아니라 도메인 중립성만 허용되는 얇은 커널이어야 한다.

### 2.5 경계 규칙
- route→repository 직접 결합 금지. route는 service/application layer 또는 주입된 port만 호출한다.
- plane은 조립 전용이다. plane 코드 안에 도메인 규칙, persistence, policy 를 두지 않는다.
- service 코드는 도메인 규칙의 소유자다. route/plane/web 에 정책을 밀어넣지 않는다.
- FE 는 `EntityConfig.service` / `EntityConfig.entity` registry 를 canonical contract 로 사용한다.
- FE 에서 generated OpenAPI 타입은 계약 보조물이지 단독 진실 출처가 아니다.
- direct `apiFetch` 는 예외 경로만 허용하고, 예외는 명시된 화면/액션 단위로만 유지한다.
- deploy/docs 숫자와 경로는 실측 기준과 일치해야 한다. prose 수치가 실측과 다르면 prose를 stale 로 본다.

### 2.6 FE guardrail
- OpenAPI drift 발생 시 generated type/문서 동기화를 먼저 확인한다.
- `EntityConfig` service-key drift 발생 시 registry 우선으로 차단한다.
- generic CRUD 밖 direct `apiFetch` 우회는 4개 실측 화면처럼 예외 목록으로만 관리한다.

### 2.7 deploy/docs drift 원칙
- `deploy/catalog/services.yaml` 의 canonical count 는 실측 YAML key 집합이다. 현재 기준선은 43개다.
- `deploy/catalog/planes.yaml` 에 `includes:` 가 없으므로, 런타임 매핑의 executable truth 는 `planes/*/main.py` 와 worker `_EVENT_DOMAINS` 를 함께 읽는 것이다.
- `docs/INDEX.md`, `ARCHITECTURE-MAP.md`, CI 스크립트의 경로/숫자 불일치는 리팩토링 명분이 아니라 drift 신호다.

### 2.8 wave 종료 정의
한 wave 는 아래 3조건이 모두 만족될 때만 종료한다.

1. **deployable**: 렌더링/부팅/조립 기준이 현재 구조와 일치한다.
2. **rollbackable**: git revert 또는 동등한 되돌리기 경로가 유지된다.
3. **test-green**: 해당 wave 에 걸린 검증이 모두 통과한다.

## 3. 대안(Alternatives Considered)

### 대안 A — 하이브리드 구조
- 설명: 도메인 중심 코드 + 6 Runtime Plane + thin shared kernel 을 함께 고정한다.
- 장점: Task 1 실측의 backend/FE/deploy drift 를 가장 적은 변경으로 흡수한다.
- 단점: 코드 조직과 런타임 조립을 동시에 이해해야 한다.
- 채택하지 않은 이유: 없음. 채택한다.

### 대안 B — 순수 레이어 중심 재편
- 설명: presentation/service/repository 같은 수직 레이어만 기준으로 전면 재편한다.
- 장점: 개념이 단순하다.
- 단점: 6 Runtime Plane 실측과 충돌하고, `deploy/catalog/planes.yaml` 과 `planes/*/main.py` 의 실행형 truth 를 설명하지 못한다.
- 채택하지 않은 이유: 런타임 경계와 코드 조직을 하나의 축으로 오해하게 만든다.

### 대안 C — 현 상태 유지(Do Nothing)
- 설명: 문서와 실측 drift 를 유지한 채 리팩토링을 진행하지 않는다.
- 장점: 단기 변경 비용이 없다.
- 단점: 184/114 route→repository 위반, FE registry drift, catalog mismatch 를 그대로 둔다.
- 채택하지 않은 이유: 경계 붕괴를 고착화한다.

## 4. 근거(Rationale)

| 평가 축 | 선택안 점수 | 비고 |
|---------|------------|------|
| 비용(인력·시간·운영) | 4/5 | 기존 6 plane 과 48/43 drift 를 동시에 무시하지 않는다 |
| 리스크(보안·가용성·데이터 손실) | 5/5 | route→repository, FE bypass, catalog drift 를 가드레일로 차단 |
| 운영(롤백·모니터링·일상 부담) | 4/5 | wave 종료 조건이 명확하다 |
| 팀 역량(학습 곡선·이해 가능성) | 4/5 | 도메인 중심 + plane 조립 모델이 현재 코드베이스와 정합적이다 |

- **결정적 근거**: Task 1 실측은 경계 위반이 backend/FE/deploy 전반에 동시에 존재하며, 단일 레이어 재편으로는 설명되지 않는다.
- **수용한 트레이드오프**: 코드 조직과 런타임 조립을 별도 축으로 이해해야 한다.

## 5. 영향(Consequences)

### 5.1 긍정적 영향
- shared kernel 비대화를 막을 수 있다.
- plane 은 조립 전용으로 유지돼 책임이 선명해진다.
- FE registry/service-key drift 와 direct apiFetch bypass 를 분리해서 다룰 수 있다.
- docs/CI/catalog drift 를 구조적 신호로 분류할 수 있다.

### 5.2 부정적 영향 / 리스크
- 초기에는 경계 규칙이 많아 보인다.
- 기존 문서 숫자와 실측 숫자의 불일치가 더 눈에 띈다.
- route→repository 위반이 많은 영역은 후속 wave 에서 정리 부담이 크다.

### 5.3 마이그레이션 / 호환성
- 기존 외부 API 경로는 유지한다.
- plane 수는 6개로 유지한다.
- legacy 문서 수치/경로는 즉시 삭제하지 않고 stale 표기로 관리한다.
- rollback 은 git revert 우선 원칙을 유지한다.

### 5.4 측정 지표(Success Metrics)

| 지표 | 현재 | 목표 | 측정 시점 |
|------|------|------|-----------|
| route→repository 직접 결합 | 184 / 114 | 0 / 0 | 후속 wave 종료 시 |
| FE service mapping | 375 | drift 0 | 후속 wave 종료 시 |
| generated OpenAPI type files | 2 | drift 0 | 후속 wave 종료 시 |
| direct apiFetch bypass | 4 | 예외 목록만 유지 | 후속 wave 종료 시 |
| services catalog key | 43 | prose 와 일치 | 후속 wave 종료 시 |
| planes.yaml includes | 0 | executable truth 와 합치 | 후속 wave 종료 시 |

## 6. 실행 항목(Action Items)

- [ ] Task 3 — backend 경계 가드레일 적용 범위 확정
- [ ] Task 4 — FE registry/service-key guardrail 정식화
- [ ] Task 5 — deploy/docs drift audit 기준선 재정의
- [ ] Task 7 — wave 종료 기준에 deployable / rollbackable / test-green 반영

## 7. 검증(Verification)

- [ ] docs/INDEX 에 새 ADR/보조 문서 연결 확인
- [ ] `docs/` 의 신규 문서가 Task 1 실측 숫자와 충돌하지 않음
- [ ] 후속 wave 에서 boundary audit 를 0 신규 drift 로 통과

## 8. 참고 자료

- `.sisyphus/evidence/task-1-backend-dep-graph.txt`
- `.sisyphus/evidence/task-1-frontend-coupling.txt`
- `.sisyphus/evidence/task-1-boundary-mismatches.md`
- `.sisyphus/evidence/task-1-test-ci-baseline.md`
- `docs/governance/adr/0000-template.md`
- `docs/governance/adr/0011-runtime-cluster-decomposition.md`
- `docs/governance/adr/0014-runtime-plane-decomposition.md`
- `docs/governance/adr/0003-test-strategy-and-coverage-gates.md`
- `docs/governance/adr/0007-api-stability-versioning-contract.md`
- `docs/engineering/architecture/shared-libraries.md`
- `docs/engineering/architecture/be-context-map.md`
- `deploy/catalog/services.yaml`
- `deploy/catalog/planes.yaml`
- `planes/api_plane/plane_api/main.py`
- `planes/worker_plane/plane_worker/main.py`
- `web/lib/modules/index.ts`
- `web/lib/crud/api-client.ts`

---

## 작성 가이드 체크
- [x] 선택안이 단정형 한 문장이다.
- [x] 현 상태 유지 대안을 평가했다.
- [x] Task 1 실측 숫자와 경로를 근거로 썼다.
- [x] 후속 작업은 코드가 아니라 문서 결정으로만 고정했다.
