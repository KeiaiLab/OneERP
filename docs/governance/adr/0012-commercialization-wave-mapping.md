# ADR-0012: 모듈 상용화 Wave 1~4 명세 (47 모듈 분류)

## 메타데이터

| 필드 | 값 |
|------|----|
| 상태 | Accepted |
| 채택일 | 2026-04-13 |
| 결정권자 | OneERP 아키텍처 위원회, 제품 위원회 |
| 영향 범위 | 모든 도메인 모듈, 마일스톤·로드맵, 리소스 배분 |
| 관련 ADR | ADR-0001(라벨·게이트), ADR-0002(웨이브 방법론), ADR-0011(클러스터) |
| 후속 phase | M-1.x (Wave 1), M-2.x (Wave 2), M-3.x (Wave 3), M-4.x (Wave 4) 마일스톤 |

> **본 ADR은 가변 매핑이다.** 분기 회고에서 점수 변화가 임계(±5점)를
> 넘으면 본 ADR을 supersede하는 새 ADR로 매핑을 갱신한다.
> ADR-0001(정의)·ADR-0002(방법론)는 불변, 본 ADR(매핑)만 갱신한다.

## 1. 맥락(Context)

ADR-0002는 모듈 분류 **방법론**(4축 100점 점수표 + 단일 활성 웨이브
원칙)을 정의했다. 본 ADR은 그 방법론을 `docs/generated/INDEX.md`의
**47개 모듈에 실제 적용한 결과**다.

분류 절차:
1. 각 모듈에 대해 ADR-0002 §6의 4축(매출 영향·의존도·운영 리스크·
   사용 빈도) 점수를 산출.
2. 합산 점수를 4구간(80~100, 60~79, 40~59, 0~39)에 매핑.
3. 의존성 그래프(`docs/engineering/data/er-entities.md`)로 의존받는
   모듈이 의존하는 모듈과 같은 또는 이른 웨이브에 위치하는지 검증.
4. 동률·경계 모듈은 의존도 축 우선으로 위치 결정.

근거 인벤토리:
- `docs/generated/INDEX.md` — 47 모듈
- `docs/engineering/data/er-entities.md`
- `docs/engineering/architecture/be-context-map.md`
- `docs/product/scope/03-e2e-scenarios.md` (5대 시나리오)
- `docs/onboarding/01-architecture-overview.md` 구독 플랜 매트릭스
  (Starter/Business/Enterprise)

## 2. 결정(Decision)

47개 모듈을 다음 4 웨이브로 분류한다.

- **Wave 1 (재무·운영 핵심) — 12 모듈**: gateway, directory, accounting,
  hr, payroll, selling, buying, stock, expenses, projects, crm, portal
- **Wave 2 (운영 확장) — 13 모듈**: manufacturing, quality, assets,
  maintenance, ecommerce, pos, subscriptions, integration-hub, calendar,
  documents, mail, messenger, board
- **Wave 3 (지원·전문) — 14 모듈**: consolidation, esg, compliance, clm,
  ehs, plm, tms, fleet, advanced-planning, marketing, marketing-automation,
  gtm, lms, workreport
- **Wave 4 (확장·차별화) — 8 모듈**: analytics, rpa, iot, knowledge,
  wiki, survey, reservation, rental

각 웨이브의 진입 조건·완료 조건·예상 기간은 §6에 정의한다.

- **범위 In**: 47개 ERD 모듈.
- **범위 Out**: 신규 ERD 추가 시 본 ADR을 supersede하는 새 ADR로 분류.
- **발효 시점**: 즉시. Wave 1을 활성 웨이브로 설정.

## 3. 4축 점수표 (47 모듈 전수)

| # | 모듈 | 매출(30) | 의존(30) | 리스크(20) | 빈도(20) | 합계 | Wave | 클러스터 |
|---|------|----------|----------|-----------|----------|------|------|---------|
| 1 | gateway | 30 | 30 | 18 | 20 | **98** | 1 | gateway |
| 2 | accounting | 30 | 30 | 20 | 16 | **96** | 1 | finance |
| 3 | hr | 30 | 30 | 18 | 16 | **94** | 1 | hr |
| 4 | directory | 22 | 30 | 18 | 20 | **90** | 1 | portal |
| 5 | selling | 30 | 22 | 18 | 20 | **90** | 1 | sales |
| 6 | buying | 30 | 22 | 18 | 16 | **86** | 1 | procurement |
| 7 | stock | 30 | 22 | 14 | 20 | **86** | 1 | scm-core |
| 8 | payroll | 30 | 14 | 20 | 10 | **74** → **승급** | 1 | hr |
| 9 | crm | 14 | 22 | 8 | 20 | **64** → **승급** | 1 | sales |
| 10 | expenses | 22 | 14 | 14 | 16 | **66** → **승급** | 1 | procurement |
| 11 | projects | 22 | 22 | 8 | 16 | **68** → **승급** | 1 | collab |
| 12 | portal | 14 | 22 | 18 | 20 | **74** → **승급** | 1 | portal |
| 13 | manufacturing | 22 | 22 | 14 | 10 | **68** | 2 | scm-core |
| 14 | quality | 22 | 14 | 14 | 10 | **60** | 2 | scm-core |
| 15 | assets | 22 | 14 | 14 | 10 | **60** | 2 | assets |
| 16 | maintenance | 22 | 7 | 14 | 10 | **53** → **승급** | 2 | scm-core |
| 17 | ecommerce | 22 | 14 | 14 | 16 | **66** | 2 | commerce |
| 18 | pos | 22 | 14 | 14 | 16 | **66** | 2 | commerce |
| 19 | subscriptions | 22 | 14 | 14 | 10 | **60** | 2 | commerce |
| 20 | integration-hub | 14 | 22 | 14 | 10 | **60** | 2 | integration-hub |
| 21 | calendar | 14 | 14 | 8 | 20 | **56** → **승급** | 2 | collab |
| 22 | documents | 14 | 22 | 14 | 16 | **66** | 2 | collab |
| 23 | mail | 14 | 7 | 8 | 16 | **45** → **승급** | 2 | portal |
| 24 | messenger | 14 | 7 | 8 | 20 | **49** → **승급** | 2 | portal |
| 25 | board | 5 | 7 | 3 | 16 | **31** → **승급** | 2 | collab (사용빈도 보정) |
| 26 | consolidation | 22 | 7 | 20 | 5 | **54** | 3 | finance |
| 27 | esg | 14 | 7 | 14 | 5 | **40** | 3 | finance |
| 28 | compliance | 22 | 14 | 20 | 5 | **61** | 3 | compliance |
| 29 | clm | 14 | 7 | 14 | 5 | **40** | 3 | compliance |
| 30 | ehs | 14 | 7 | 14 | 5 | **40** | 3 | compliance |
| 31 | plm | 22 | 14 | 8 | 5 | **49** | 3 | assets |
| 32 | tms | 22 | 7 | 14 | 5 | **48** | 3 | logistics |
| 33 | fleet | 14 | 7 | 14 | 5 | **40** | 3 | logistics |
| 34 | advanced-planning | 14 | 14 | 8 | 5 | **41** | 3 | logistics |
| 35 | marketing | 14 | 7 | 8 | 10 | **39** → **승급** | 3 | marketing |
| 36 | marketing-automation | 14 | 7 | 8 | 10 | **39** → **승급** | 3 | marketing |
| 37 | gtm | 14 | 7 | 8 | 5 | **34** → **승급** | 3 | marketing |
| 38 | lms | 14 | 7 | 8 | 10 | **39** → **승급** | 3 | learning |
| 39 | workreport | 14 | 7 | 8 | 16 | **45** | 3 | learning |
| 40 | analytics | 10 | 22 | 8 | 16 | **56** → **강등** | 4 | analytics |
| 41 | rpa | 10 | 7 | 8 | 5 | **30** | 4 | rpa |
| 42 | iot | 10 | 7 | 14 | 5 | **36** | 4 | iot |
| 43 | knowledge | 5 | 7 | 3 | 10 | **25** | 4 | collab |
| 44 | wiki | 5 | 7 | 3 | 10 | **25** | 4 | collab |
| 45 | survey | 5 | 2 | 3 | 5 | **15** | 4 | collab |
| 46 | reservation | 14 | 2 | 8 | 10 | **34** | 4 | sales |
| 47 | rental | 14 | 7 | 8 | 5 | **34** | 4 | sales |

> 합계 옆의 "**승급**"/"**강등**" 표기는 점수 구간 외 배정 사유를
> §4에서 설명한다.

## 4. 구간 외 배정 사유

분류는 점수가 1차 기준이지만 다음 4개 보정 규칙을 우선 적용한다.

### 4.1 의존성 보정 (의존받는 쪽이 먼저)
- **payroll, crm, expenses, projects, portal**: 점수 60~74로 본래 Wave 2
  경계지만, 다음 모듈들이 이들에 의존하므로 Wave 1로 승급:
  - selling/buying이 expenses·projects를 참조
  - selling/crm/portal이 directory와 함께 시작 가능해야 함
  - payroll은 hr 직원 마스터의 즉시 소비자
- **maintenance, calendar, mail, messenger, board**: 본래 Wave 3 경계
  점수지만 collab/portal 클러스터가 Wave 2 완성도를 갖춰야 사용자
  체류가 발생하므로 Wave 2로 승급.

### 4.2 클러스터 결합 보정
- **marketing, marketing-automation, gtm, lms**: 본래 Wave 4 경계
  점수지만 같은 클러스터(marketing, learning) 모듈이 Wave 3 안에서
  함께 도달해야 운영 효율 → Wave 3으로 승급.

### 4.3 사용 빈도 보정
- **board**: 합계 31점이지만 일일 사용자 비율이 높아 Wave 2 승급.

### 4.4 강등 (의존성 역방향)
- **analytics**: 합계 56점이지만 다른 모듈의 데이터를 소비하므로
  Wave 1·2가 데이터를 생성하기 전에 분석할 의미가 없음 → Wave 4 강등.

## 5. 의존성 검증

다음 의존 관계가 본 매핑에서 위반되지 않음을 확인한다(요약).

```text
gateway ──→ (모든 모듈 진입)
directory ──→ hr, portal, accounting (인적 마스터)
hr ──→ payroll, expenses, projects, workreport, lms
accounting ──→ selling, buying, expenses, payroll, consolidation
stock ──→ selling, buying, manufacturing, maintenance, ecommerce, pos
selling ──→ pos, subscriptions, ecommerce, crm
buying ──→ expenses, integration-hub
projects ──→ workreport, advanced-planning
crm ──→ marketing, marketing-automation, gtm
manufacturing ──→ quality, plm
assets ──→ maintenance, plm
compliance ──→ clm, ehs
analytics ←── (모든 모듈)
```

규칙: "의존받는 모듈은 의존하는 모듈과 같은 또는 이른 웨이브."
모든 화살표가 "이른 웨이브 → 늦은 웨이브" 또는 "동일 웨이브"를
만족함을 검증 완료.

## 6. 웨이브 명세

### 6.1 Wave 1 — 재무·운영 핵심 (12 모듈)

**모듈**: gateway, directory, accounting, hr, payroll, selling, buying,
stock, expenses, projects, crm, portal

**진입 조건**:
- ADR-0008 관측성 baseline 인프라 가동 (Prometheus/Loki/Tempo 가용)
- ADR-0006 인가 코어(`authorize()`) 구현 완료
- ADR-0005 `TenantScopedRepository` 강제 활성

**완료 조건**:
- 12 모듈 모두 `pre-commercial` 라벨 (ADR-0001 §7) 도달
- 5대 E2E 시나리오 통과율 ≥ 95% (`docs/product/scope/03-e2e-scenarios.md`)
- 구독 플랜 "Starter"(`selling, buying, stock, accounting`) 4 모듈은
  `commercial-ready` 도달

**예상 기간**: 6개월 (M-1.1 ~ M-1.6)

**클러스터 매핑**: gateway, finance, hr, sales, procurement, scm-core,
collab(projects만), portal

**위험**:
- 인가 코어 지연이 12 모듈 모두를 차단
- 5대 E2E 시나리오 자동화 부재 → 수동 회귀 부담
- 완화: ADR-0003 nightly E2E 5개 중 우선 3개(판매·구매·재고)부터

### 6.2 Wave 2 — 운영 확장 (13 모듈)

**모듈**: manufacturing, quality, assets, maintenance, ecommerce, pos,
subscriptions, integration-hub, calendar, documents, mail, messenger, board

**진입 조건**:
- Wave 1의 12 모듈 100% `pre-commercial` 또는 그 이상
- Tier 2 멀티테넌시(ADR-0005) 마이그레이션 도구 동작
- ADR-0010 카나리 자동 중단 검증 완료

**완료 조건**:
- 13 모듈 모두 `pre-commercial` 도달
- 구독 플랜 "Business" 모든 모듈이 `commercial-ready`
- integration-hub가 외부 시스템 3종 이상 검증

**예상 기간**: 5개월 (M-2.1 ~ M-2.5)

**위험**:
- manufacturing/scm-core 통합이 Wave 1 stock과 강결합 → 회귀 영향 큼
- ecommerce/pos는 외부 결제·재고 동기화 → integration-hub 의존
- 완화: 클러스터 단위 카나리 + ADR-0009 분기 리허설로 격리 검증

### 6.3 Wave 3 — 지원·전문 (14 모듈)

**모듈**: consolidation, esg, compliance, clm, ehs, plm, tms, fleet,
advanced-planning, marketing, marketing-automation, gtm, lms, workreport

**진입 조건**:
- Wave 2 완료
- ADR-0007 v1 → v2 전환 정책 정립(필요 시)
- 데이터 등급 A 모든 모듈 분기 리허설 1회 통과(ADR-0009)

**완료 조건**:
- 14 모듈 `pre-commercial` 이상
- 구독 플랜 "Enterprise" 핵심 부가 기능 commercial-ready
- 컴플라이언스(GDPR/SOX/ISO) 산업별 가이드 발행

**예상 기간**: 6개월 (M-3.1 ~ M-3.6)

**위험**:
- compliance/clm/ehs는 산업별 요구가 분기될 수 있음 → 핵심만 commercial,
  산업 변형은 별도 phase
- consolidation은 다중 회사 통합 회계 → 회계(Wave 1) 데이터 정합성에 의존

### 6.4 Wave 4 — 확장·차별화 (8 모듈)

**모듈**: analytics, rpa, iot, knowledge, wiki, survey, reservation, rental

**진입 조건**:
- Wave 3 완료
- analytics는 Wave 1~3의 데이터 모델이 안정 (스키마 변경 빈도 분기 X1 미만)

**완료 조건**:
- 8 모듈 전부 23/23 기준 통과 (commercial-ready)
- analytics는 BI 표준 5개 대시보드 발행
- rpa/iot는 파일럿 고객 1곳 이상 적용 검증

**예상 기간**: 4개월 (M-4.1 ~ M-4.4)

**위험**:
- analytics가 데이터 변경에 흔들림 → ADR-0007 v1 stable 후 진행
- iot/rpa는 시장 검증 부족 → beta 고정으로 commercial 강제 회피

## 7. 웨이브 전환 게이트

| 게이트 | 누가 | 무엇을 |
|--------|------|--------|
| 진입 점검 | 아키텍처 위원회 | §6 진입 조건 자동 점검 결과 보고 |
| 활성 웨이브 단일성 | 인프라팀 | 비활성 웨이브 phase 진입 시 CI 경고 |
| 완료 선언 | 제품 위원회 | §6 완료 조건 + 분기 회고 보고서 |
| 다음 웨이브 활성화 | 아키텍처 + 제품 위원회 합의 | 본 ADR을 supersede하는 ADR(또는 동일 ADR 유효 확인) |

## 8. 분기 회고

ADR-0002 §11 양식 사용. 본 ADR 갱신 트리거:
- 모듈 점수 ±5점 이상 변동
- 신규 모듈 추가
- 의존 그래프 변경 (외래 참조 추가/삭제)
- 클러스터 변경(ADR-0011 supersede)

회고 결과는 `docs/governance/wave-retrospective-YYYYQN.md`로 보존.

## 9. 영향(Consequences)

### 9.1 긍정적
- 47 모듈에 대한 우선순위가 객관 점수 + 의존성 검증으로 합의됨
- 마일스톤(M-1~M-4)이 본 매핑에 1:1로 매핑됨
- 후순위 모듈 오너는 명확한 시점 안내 받음

### 9.2 부정적
- Wave 4 모듈(analytics, rpa, iot, wiki 등) 오너는 21개월 이상 대기
- Wave 1의 12 모듈 동시 진행은 인지 부하 큼 → 클러스터 단위 phase 분할로 완화

### 9.3 호환성
- 기존 진행 중 작업은 §6 클러스터 매핑에 따라 활성/대기 분류
- ADR-0011 클러스터(19개)와 본 ADR 모듈(47개)은 N:M 관계, 클러스터
  내부 모듈은 함께 활성화

### 9.4 측정 지표

| 지표 | 현재 | 목표 |
|------|------|------|
| Wave 1 모듈 평균 라벨 | alpha | pre-commercial(6개월) |
| 활성 웨이브 외 작업 비중 | n/a | < 20% |
| 의존성 위반 차단 횟수 | 0 | (측정 시작) |
| 본 ADR supersede 빈도 | n/a | 분기 ≤ 1회 (안정성 지표) |

## 10. 실행 항목

- [ ] 아키텍처 위원회 — Wave 1 진입 조건 자동 점검 스크립트 — 2026-04-30
- [ ] 모듈 오너 — 자기 모듈 점수에 동의/이의 — 2026-04-25
- [ ] 인프라팀 — 활성 웨이브 외 phase 경고 메커니즘 — 2026-05-15
- [ ] 제품 위원회 — Wave 1 마일스톤(M-1.1~M-1.6) 분기 — 2026-04-30
- [ ] SRE — 5대 E2E 자동화 우선순위 합의 — 2026-04-30

## 11. 검증

- [ ] `scripts/audit/dep_graph.py` 결과와 §5 의존 그래프 일치
- [ ] `scripts/audit/commercial-readiness.py`가 웨이브별 라벨 분포 보고
- [ ] 분기마다 §3 점수표 재산출

## 12. 부록 A — 클러스터 × 웨이브 매트릭스

| 클러스터 | Wave 1 | Wave 2 | Wave 3 | Wave 4 |
|---------|--------|--------|--------|--------|
| gateway | gateway | | | |
| sales | selling, crm | | | reservation, rental |
| commerce | | ecommerce, pos, subscriptions | | |
| scm-core | stock | manufacturing, quality, maintenance | | |
| procurement | buying, expenses | | | |
| finance | accounting | | consolidation, esg | |
| hr | hr, payroll | | | |
| learning | | | lms, workreport | |
| collab | projects | calendar, documents, board | | knowledge, wiki, survey |
| portal | directory, portal | mail, messenger | | |
| logistics | | | tms, fleet, advanced-planning | |
| marketing | | | marketing, marketing-automation, gtm | |
| compliance | | | compliance, clm, ehs | |
| assets | | assets | plm | |
| analytics | | | | analytics |
| rpa | | | | rpa |
| iot | | | | iot |
| integration-hub | | integration-hub | | |
| automation-orchestrator | (인프라성 — Wave 1과 동기 진행) | | | |

## 13. 부록 B — 예상 마일스톤 일정

| 마일스톤 | 시작 | 종료 | 결과 |
|---------|------|------|------|
| M-1.1~1.6 | 2026-05 | 2026-10 | Wave 1 12 모듈 pre-commercial+ |
| M-2.1~2.5 | 2026-11 | 2027-03 | Wave 2 13 모듈 pre-commercial+ |
| M-3.1~3.6 | 2027-04 | 2027-09 | Wave 3 14 모듈 pre-commercial+ |
| M-4.1~4.4 | 2027-10 | 2028-01 | Wave 4 8 모듈 beta+ |

총 21개월 예상. 단일 활성 웨이브 원칙 + ADR-0002 예외(분기 3건 한도)
적용 시.

## 14. 참고 자료

- `docs/generated/INDEX.md`
- `docs/engineering/data/er-entities.md`
- `docs/engineering/architecture/be-context-map.md`
- `docs/product/scope/03-e2e-scenarios.md`
- `docs/onboarding/01-architecture-overview.md` (구독 플랜)
- ADR-0001 (정의), ADR-0002 (방법론), ADR-0011 (클러스터)
