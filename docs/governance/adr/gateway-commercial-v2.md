---
status: accepted
date: 2026-04-22
decision: gateway 모듈을 Commercial Grade v2 첫 수직 완성 대상으로 선정하고 23/23 PASS 를 Spec II 범위로 묶는다
consequences: gateway 모듈의 실증 증거 커버리지가 baseline (3셀) 에서 23 셀로 확장 · T3 staging 드릴 180일 주기 유지 · 회귀 0 유지 필수 · 이 경험을 Spec III~V 에 템플릿화
---

# ADR — gateway 모듈 Commercial Grade v2 승격 결정

## 배경

OneERP 47 모듈 중 ADR-0012 점수 98 로 최상위인 gateway 모듈을 **Commercial Grade v2 첫 수직 완성 모듈**로 선정한다. 이 선정은 다음 세 가지 전제에 기반한다.

1. **Commercial Grade v2 엔진의 현실성 검증** — 47 모듈 × 23 게이트 = 1,081 셀 감사 체계가 이론상 설계됐지만, 실제 한 모듈을 23/23 PASS 로 끌어올리는 과정에서 나오는 감사 기준의 오류·과함을 조기 발견해야 한다. gateway 는 복잡도가 높으면서도 범위가 명확한 모듈이라 이 검증에 적합하다.
2. **v1 시대의 gateway 성과 재활용** — Ralph-Loop iter 4 에서 gateway 에 G4-3/4/5 드릴 3건이 최초로 작성됐고, iter 10 에서 G4-2 런북이 초기 버전으로 존재했다. 이 자산들은 v2 기준을 충족하도록 보강 가능한 상태로, 완전 재작성 대비 비용이 적다.
3. **의존 모듈 파급 효과** — gateway 는 27 개 다운스트림 모듈이 API 진입점으로 사용한다. gateway 가 commercial-ready 되면 하위 모듈들의 G1-2 (OpenAPI) · G3-1 (authN) 작업이 gateway 를 신뢰 기반으로 삼을 수 있어 전체 진행 속도가 빨라진다.

## 결정 배경 (대안 비교)

| 대안 | 장점 | 단점 | 결론 |
|---|---|---|---|
| **A. gateway 수직 완성** (선정) | 최상위 점수 · v1 자산 재활용 · 다운스트림 파급 | 복잡도 높음 | ✅ 선정 |
| B. accounting 수직 완성 | 재무 무결성 실증 · 감사 정확도 | 도메인 특화로 일반화 어려움 | Spec III 로 이관 |
| C. 여러 모듈 동시 부분 완성 | 평면적 진전 | 수직 깊이 검증 안 됨 · v2 엔진 현실성 미검증 | 거부 |
| D. 감사만 조정 | 리스크 최소 | 실제 작동 증거 없음 — Spec I 원래 비판과 동일 | 거부 |

## 결정 사항

1. **Spec I 범위 (이 세션)**: gateway × {G1-1 ADR, G1-4 단위 테스트, G4-2 런북} 3 셀 PASS — 엔진 작동 증명
2. **Spec II 범위**: gateway 나머지 20 게이트 (G1-2/3/5, G2-*, G3-*, G4-1/3/4/5, G5-*) → 23/23 commercial-ready
3. **T3 드릴 주기**: G4-3 백업 · G4-4 롤백 · G4-5 On-call 은 180일 주기 staging 재실행 의무화
4. **회귀 방지**: gateway 가 commercial-ready 도달 이후, 해당 라벨 하락 시 블로커 #9 발동
5. **확산 템플릿**: gateway 완성 과정에서 나온 artisan·scribe·executor 패턴을 Spec III (accounting + hr) 에서 재사용

## 결과

### 즉각 영향 (Spec I 완료 시점)

- gateway 모듈 라벨: `none` → `alpha` (G1-1 + G1-2 PASS 조건) 또는 `beta` (G1-1/2/3/4 + G3-1/4 + G4-2 중 충족분)
  - 파일럿 3 셀(G1-1, G1-4, G4-2) 은 `beta` 7조건 중 3개 충족 — 라벨 자체는 `alpha` 이상 상향 가능 여부가 G1-2 에 달림
  - Spec II 에서 G1-2 완성 시 beta 승격 가능
- 전체 47 모듈 baseline: 0/1081 → 3/1081 (0.28%)
- Commercial Engine 의 5 에이전트 (planner/artisan/scribe/executor/reviewer) 전원 dispatch 경험 확보

### 중기 영향 (Spec II 완료 시점, 예상 3~5 세션)

- gateway 최초로 `commercial-ready` 달성 · 47 모듈 중 1/47
- 전체 baseline 3 → 23/1081 (2.1%)
- artifacts/ 구조 실전 검증 — 증거 무결성 체인·20% replay 실측
- G4-3/4/5 staging 드릴 실제 실행 경험 — T3 증거 최초 생성

### 장기 영향 (Spec III~V 완료 시 = ONEERP_COMPLETE)

- 전체 47 모듈 commercial-ready · 1,081/1,081 PASS
- Spec II gateway 경험이 템플릿화되어 Wave1 11 모듈 확산 비용 절감
- 품질 게이트 (ruff/ty/biome) 0 errors 달성 — `scripts/audit/commercial_readiness.py --verify --strict` exit 0

## 위험 및 완화

| 위험 | 발생 확률 | 영향 | 완화 |
|---|---|---|---|
| Spec II 에서 감사 기준 비현실 발견 | 중 | Spec II 범위 확장 필요 | ADR-0016 는 living doc — 조정 허용 |
| gateway 의존 모듈 작업이 gateway 완성 전 시작 | 중 | 재작업 발생 | Spec III 는 gateway Spec II 완료 후에만 착수 |
| T3 staging 환경 미준비 | 높음 | G4-3/4/5 불가 | Spec II 착수 전 staging 환경 확보 사전작업 |
| ruff/ty 회귀 | 낮음 | 품질 게이트 실패 | Task 마다 lint 게이트 · CI 에서 재검증 |

## 참조

- Spec: `docs/superpowers/specs/2026-04-22-commercial-grade-v2-triple-resource-design.md`
- Plan: `docs/superpowers/plans/2026-04-22-commercial-grade-v2-engine.md`
- ADR-0001: 23 품질 기준 정본
- ADR-0012: Wave 매핑 (gateway 점수 98 최상위)
- v1 gateway 드릴: `docs/ops/drills/G4-{3,4,5}/2026-04-21-gateway.md` (iter 4 성과)

## 후속 작업

1. Spec I 파일럿 완료 — Task 15/16/17 진행 중
2. Spec I 종료 후 Spec II 브레인스토밍 — gateway 나머지 20 게이트 세부 계획
3. staging 환경 접근 권한 확보 (T3 작업 착수 전)
4. gateway 확장 이후 Spec III 착수 대기 — accounting + hr

## 23 게이트 진행 체크포인트

Spec II 진행 중 이 표를 수시 갱신한다. `scripts/audit/commercial_readiness.py --module gateway` 결과와 동기화.

### G1 설계·API·코드
- G1-1 ADR: PASS (본 문서)
- G1-2 OpenAPI: pending (Spec II)
- G1-3 통합 테스트: pending (Spec II)
- G1-4 단위 테스트: PASS (파일럿)
- G1-5 UI Playwright: pending (Spec II)

### G2 성능·관측·국제화
- G2-1 SLO: pending — Prometheus 30일 번다운 필요
- G2-2 부하: pending — k6 1000rps × 5분
- G2-3 성능 회귀: pending — 30일 0건 로그
- G2-4 chaos: pending — fault-inject staging 실행
- G2-5 i18n: pending — ko/en/ja 95% 커버리지

### G3 보안·감사·의존성
- G3-1 authN: pending — OIDC · JWT rotation · 7종 pytest
- G3-2 시크릿: pending — ExternalSecrets · rotation 자동화
- G3-3 RBAC: pending — OPA 정책 · 테스트 5+
- G3-4 감사 이벤트: pending — mutation route 전수 emit
- G3-5 의존성: pending — high/critical CVE 0

### G4 운영·복구·드릴
- G4-1 모니터링: pending — Grafana overview + 알림 5+
- G4-2 런북: PASS (파일럿)
- G4-3 백업 드릴: pending — T3 staging · 180일 주기
- G4-4 롤백 드릴: pending — 동상
- G4-5 On-call 드릴: pending — 호출 체인 + 응답 시간

### G5 문서·교육·UAT
- G5-1 매뉴얼: pending — ≥250라인 + 스크린샷 5+
- G5-2 튜토리얼: pending — ≥300라인 + code block 10+
- G5-3 UAT: pending — Given/When/Then 5+ + 승인자 서명
