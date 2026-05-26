# OneERP Ralph-Loop 전체 상용 완성 설계서

## 1. 배경

OneERP는 이미 상용화 정의와 측정 자산을 상당 부분 갖고 있다.
정본 규칙은 [`ADR-0001`](../governance/adr/0001-commercial-grade-definition.md)와
[`ADR-0012`](../governance/adr/0012-commercialization-wave-mapping.md)에 있고,
프로그램 백본은 [`.planning/ROADMAP.md`](/Users/phil/WorkSpace/apps/OneErp/.planning/ROADMAP.md)와
[`.planning/program/releases/RELEASE-CRITERIA.md`](/Users/phil/WorkSpace/apps/OneErp/.planning/program/releases/RELEASE-CRITERIA.md)에 있다.
또한 `scripts/audit/commercial_readiness.py`는 모듈별 23 게이트 통과 현황을 계측할 수 있다.

문제는 이 자산들이 아직 "47모듈 전체 상용 완성"을 향한 단일 운영 체계로 묶여 있지 않다는 점이다.
현재 문서는 `M7 파일럿 출시`와 `전체 상용 완성`을 함께 다루지만, Wave 4 완료 정의와 전수 상용화 정의가 충돌한다.
따라서 Ralph-loop를 단순 반복 도구가 아니라, 마스터 플랜과 실측을 동시에 강제하는 운영 오케스트레이터로 재설계해야 한다.

## 2. 사용자 결정과 가정

이번 설계는 아래 사용자 결정을 전제로 한다.

- 최종 목표는 `M7 파일럿 출시`가 아니라 `47모듈 전체 상용 완성`이다.
- 증거 수준은 `audit + CI + stack smoke`가 아니라 `출시급 실측`이다.
- 실측에는 핵심 업무 흐름 E2E, Playwright 기반 웹 검증, 성능, 복구, 운영 리허설이 포함된다.

추가 가정은 다음과 같다.

- 최종 완료 기준은 `47모듈 × 23 게이트 = 1,081/1,081 GREEN`이다.
- `ADR-0012`의 `Wave 4는 beta 이상이면 완료` 문구는 현 목표와 충돌하므로 개정 대상이다.
- `docs/INDEX.md`가 가리키는 `docs/product/plans/2026-02-09-master-plan.md`는 현재 존재하지 않으므로, 실제 운용 정본은 `.planning/ROADMAP.md`와 `.planning/program/releases/RELEASE-CRITERIA.md`로 본다.

## 3. 접근안 비교

### 접근안 A. Phase-first

- `.planning/ROADMAP.md`의 Phase 1~7을 중심으로 루프를 운용한다.
- 장점: 현재 마스터 플랜과의 정합성이 가장 높고, 사람에게 설명하기 쉽다.
- 단점: `1,081 셀`의 누락 게이트가 가려질 수 있고, "Phase는 끝났지만 상용 게이트는 덜 닫힌 상태"를 허용하기 쉽다.

### 접근안 B. Gate-first

- `scripts/audit/commercial_readiness.py`의 미통과 셀만을 직접 공략한다.
- 장점: 최종 완료 정의와 직접 연결되며, 진척률을 수치로 관리하기 쉽다.
- 단점: 사용자 흐름, 운영 준비, 출시 리허설이 파편화되기 쉽고, 제품 경험보다 숫자 채우기로 흐를 위험이 있다.

### 접근안 C. Hybrid dual-control

- `ROADMAP` Phase를 프로그램 백본으로 유지하되, 실제 작업 선택은 `모듈 × 게이트` 미통과 셀에서 한다.
- 각 Phase 종료와 Wave 전환은 숫자뿐 아니라 `출시급 실측` 통과를 강제한다.
- 장점: 사용자가 요구한 "마스터 플랜 기준"과 "전체 상용 완성 실측"을 동시에 만족시킨다.
- 단점: 상태 문서, 정지 조건, 리허설 스크립트가 더 엄격하게 설계돼야 한다.

### 선택

이번 설계는 **접근안 C. Hybrid dual-control**을 채택한다.
이 선택은 `마스터 플랜을 따르되, 완료 판정은 숫자와 실측 모두로 잠근다`는 원칙을 의미한다.

## 4. 운영 아키텍처와 완료 판정

운영 구조는 `Phase spine + Gate engine + Release rehearsal` 3중 제어로 둔다.

- `Phase spine`
  - 실제 프로그램 운영 순서는 `.planning/ROADMAP.md`의 Phase 1~7을 유지한다.
  - 즉, 이벤트 체인 안정화 → 핵심 운영 E2E → 협업/UI → 대시보드/출력 → 운영 인프라 → 통합 QA/성능/보안 → 문서/파일럿 검증 순서를 백본으로 삼는다.
- `Gate engine`
  - iteration의 실제 작업 선택은 `scripts/audit/commercial_readiness.py`가 산출하는 미통과 셀에서만 한다.
  - "다음 할 일"은 넓은 문장형 TODO가 아니라 `모듈 × 게이트` 단위로 고른다.
- `Release rehearsal`
  - Phase 완료나 Wave 전환은 숫자만으로 주장하지 않는다.
  - 자동 E2E, Playwright, 성능, 복구, 운영 문서 일치 검증까지 다시 돌려야만 완료로 인정한다.

최종 완료 판정은 아래 4개 조건의 AND로 둔다.

1. `47모듈 × 23게이트 = 1,081/1,081 GREEN`
2. `./scripts/ci/run.sh` 전체 통과
3. `PROFILE=plane TIMEOUT=240 ./scripts/dev/stack-smoke.sh` 통과
4. 출시급 실측 묶음 통과

여기서 출시급 실측 묶음은 핵심 업무 흐름 E2E, Playwright 기반 핵심 웹 흐름, 성능 기준, 장애/복구 리허설, 운영 문서-실행 일치 검증을 포함한다.

## 5. Iteration 운영 방식과 실측 파이프라인

한 iteration의 최소 단위는 항상 `하나의 주된 미통과 셀`이다.
예를 들면 `buying × G1-3`, `portal × G1-5`, `stock × G3-4`처럼 잡는다.
실제 구현 과정에서 선행 조건 때문에 주변 셀이 함께 닫힐 수는 있지만,
iteration 목표 자체는 항상 검증 가능한 대표 셀 하나로 고정한다.

iteration 흐름은 다음 순서로 강제한다.

1. 현재 `commercial_readiness` 결과를 읽고 타겟 셀을 선택한다.
2. 그 셀을 통과시키는 데 필요한 사용자 시나리오, 자동 테스트, 문서 증거를 역산한다.
3. 실패 테스트를 먼저 추가하거나 기존 실패를 재현한다.
4. 구현을 최소 범위로 수정한다.
5. 셀 근거 검증을 다시 돌린다.
6. 해당 모듈의 단기 회귀 검증을 돌린다.
7. audit를 재생성해 실제로 셀이 GREEN으로 바뀌었는지 확인한다.
8. 결과와 증거 경로를 진행 로그에 남긴다.

실측 파이프라인은 3층으로 분리한다.

- `L1 셀 검증`
  - OpenAPI, auth coverage, tenant isolation, audit log, runbook, user manual 같은 개별 게이트의 직접 증거
- `L2 흐름 검증`
  - Procure-to-Pay, Payroll-to-Accounting, Manufacture-to-Stock, CRM-to-Selling, Approval-Anywhere 같은 핵심 사용자 흐름 E2E
  - 웹은 Playwright를 사용한다
- `L3 출시 검증`
  - `./scripts/ci/run.sh`, `stack-smoke`, 성능 측정, 장애 주입/복구, 운영 문서 실행 일치, 파일럿 데모 시나리오 재연

원칙은 `작업은 셀 단위`, `가치는 흐름 단위`, `출시 판정은 리허설 단위`다.

## 6. 우선순위 규칙, 정지 조건, 전환 규칙

우선순위는 `정본 정합 → 활성 Wave → 현재 Phase 성공조건 → 개별 게이트` 순서로 강제한다.

실행 시작 전에 최소 두 가지 정합화가 선행되어야 한다.

1. `ADR-0012`의 `Wave 4 beta 예외`를 최종 완료 정의에 맞게 개정
2. `docs/INDEX.md`의 누락된 마스터 플랜 경로를 실제 정본 경로로 정리

그 후 작업 선택 우선순위는 아래와 같다.

1. 현재 정의와 충돌하는 정본 문서 수정
2. 활성 Wave의 미통과 셀 중 현재 Phase 성공조건에 직접 연결된 셀
3. 핵심 사용자 흐름을 막는 공통 병목 셀
4. 보안·운영 게이트처럼 여러 흐름에 재사용되는 횡단 셀
5. 문서·UAT·튜토리얼처럼 마지막에 닫아야 하는 셀

정지 조건은 기존 `HANDOFF.md`의 11개 하드 블로커를 계승하되, 아래 3개를 추가한다.

- 정본 문서 간 완료 정의 충돌이 새로 생김
- 출시급 실측이 같은 원인으로 3회 연속 실패
- `1,081 셀` pass 수는 늘지만 핵심 흐름 E2E가 2 iteration 연속 악화됨

Phase 전환은 `.planning/ROADMAP.md`의 해당 Phase 성공조건과 대응 실측 묶음이 함께 통과할 때만 허용한다.
Wave 전환은 아래 조건을 모두 만족할 때만 허용한다.

- 현재 Wave의 모든 모듈이 `23/23`
- 라벨 하락 0건
- P0/P1 회귀 0건
- 다음 Wave 선행 인프라 GREEN

즉, 단일 활성 Wave 원칙을 유지하고 "다음 것도 미리 조금" 전략은 금지한다.

## 7. 필수 산출물과 문서 구조

필수 산출물은 4묶음으로 둔다.

- `정본 규칙 문서`
  - 완료 정의, Wave 규칙, Phase 성공조건, release criteria 같은 의사결정 문서
- `자동 생성 상태 산출물`
  - `docs/generated/commercial-status.json` 같은 셀 상태 SoT
- `실측 증거 묶음`
  - E2E 로그, Playwright 결과, 성능 리포트, 복구 리허설 로그, 스택 스모크 결과
- `운영 요약 보드`
  - 사람이 보는 최종 판정판

문서 구조는 다음처럼 유지한다.

1. `docs/governance/adr/`
   - 완료 정의와 Wave 규칙 같은 결정만 둔다.
2. `docs/product/roadmap/`
   - 현재 활성 Phase, 활성 Wave, 다음 게이트, 전체 진행률 같은 지도만 둔다.
3. `docs/generated/`
   - audit, 렌더링 결과, 자동 집계표처럼 기계가 만든 상태만 둔다.
4. `artifacts/`
   - Playwright, 성능, 복구, stderr, smoke 실행 로그 같은 실측 증거만 둔다.

측정 보드는 최소 3뷰가 필요하다.

- `전역 보드`
  - `1081 중 몇 개 GREEN인지`, `모듈별 commercial-ready 현황`, `최근 7일 회귀 수`
- `출시 보드`
  - 핵심 흐름 E2E, 성능, 복구, 운영 문서 검증, 보안 점검의 최신 결과
- `정지 보드`
  - 현재 루프를 멈춰야 하는 블로커와 근거

## 8. 비목표

이번 설계의 비목표는 다음과 같다.

- 새로운 제품 기능 추가
- `ROADMAP` Phase 순서 자체를 재정의
- Wave 병렬 활성화
- UI 미관 개선만을 위한 별도 캠페인
- 근거 없는 범용 오케스트레이터 추상화

## 9. 발견사항

설계 과정에서 확인된 즉시 정합화 대상은 아래 두 가지다.

- [`docs/INDEX.md`](../INDEX.md)는 존재하지 않는 `docs/product/plans/2026-02-09-master-plan.md`를 참조한다.
- [`ADR-0012`](../governance/adr/0012-commercialization-wave-mapping.md)는 `Wave 4 beta 이상`을 완료로 보지만,
  [`docs/product/roadmap/README.md`](../product/roadmap/README.md)는 `47모듈 × 23 전수 통과`를 전체 상용으로 정의한다.

둘 다 루프 시작 전에 정리해야 한다.

## 10. 승인 상태

- 상태: 승인됨
- 승인 일시: 2026-04-16
- 승인 범위:
  - 최종 목표는 `47모듈 전체 상용 완성`
  - 증거 수준은 `출시급 실측`
  - 운영 방식은 `Hybrid dual-control`
