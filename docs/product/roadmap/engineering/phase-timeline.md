---
owner: Engineering Lead
last_updated: 2026-04-16
stale_after_days: 60
audience: engineering
---

# 작업 흐름 1~7 횡단 시간축

> 이 문서는 각 작업 흐름이 **어느 모듈 집단의 어느 품질 기준을 밀어 올리는가** 를 시간 순으로 배치한다.
> 작업 흐름 상세 계획(Task 목록·성공 기준·의존)은 `.planning/phases/0N-*/PLAN.md` 정본에만 있다.

## P1 · 이벤트 체인 안정화

- 정본: [.planning/phases/01-event-chain-stabilization/01-01-PLAN.md](../../../../.planning/phases/01-event-chain-stabilization/01-01-PLAN.md)
- 대상 범위: **전 모듈 공통**
- 주 추진 영역 (ADR-0001 정본): 기능 완전성 G1-3(통합 테스트) 전제 + 운영 준비 G4-1(관측)
- 대표 산출물: event-contracts SoT · drift 체크 스크립트 · FL1 ~ FL4 회귀

## P2 · 핵심 운영 E2E 완성

- 정본: [.planning/phases/02-core-ops-e2e/](../../../../.planning/phases/02-core-ops-e2e/)
- 대상: 모듈 집단 1 우선 + 집단 2 일부 (구매·경비·급여·제조 흐름에 닿는 모듈)
- 주 추진 영역 (ADR-0001 정본): 기능 완전성 G1-1 ~ G1-5 (ERD·API·통합·단위·UI 전면)
- 대표 산출물: Procure-to-Pay · Expense-to-Payment · Payroll · Manufacture-to-Stock E2E

## P3 · 협업·영업 흐름 + 결재 UI

- 정본: [.planning/phases/03-collab-sales-approval-ui/](../../../../.planning/phases/03-collab-sales-approval-ui/)
- 대상: 모듈 집단 1 ∩ Groupware Stream · 집단 2 CRM 포함
- 주 추진 영역 (ADR-0001 정본): 기능 완전성 G1-4·G1-5 + 보안·컴플라이언스 G3-2(권한 매트릭스)
- 대표 산출물: CRM → Selling 파이프라인 · Approval-Anywhere · 결재 웹 UI

## P4 · 대시보드·보고서 사용자 출력

- 정본: [.planning/phases/04-dashboard-reporting-ui/](../../../../.planning/phases/04-dashboard-reporting-ui/)
- 대상: 모듈 집단 1~2
- 주 추진 영역 (ADR-0001 정본): 기능 완전성 G1-5(UI) + 보안·컴플라이언스 G3-2(권한 데이터 마스킹)
- 대표 산출물: KPI 대시보드 · PDF 출력 · 권한별 데이터 마스킹

## P5 · 파일럿 운영 인프라 마감

- 정본: [.planning/phases/05-pilot-ops-infra/](../../../../.planning/phases/05-pilot-ops-infra/)
- 대상: **전 모듈 공통**
- 주 추진 영역 (ADR-0001 정본): 운영 준비 G4-1 ~ G4-5 (관측·runbook·backup·rollback·oncall 전수)
- 대표 산출물: 게이트웨이 · 배포 매니페스트 · 관측성 · 백업·복구 검증

## P6 · 통합 QA·성능·보안 검증

- 정본: [.planning/phases/06-integrated-qa/](../../../../.planning/phases/06-integrated-qa/)
- 대상: **전 모듈 공통**
- 주 추진 영역 (ADR-0001 정본): 비기능 품질 G2-1 ~ G2-5 + 보안·컴플라이언스 G3-1 ~ G3-5
- 대표 산출물: API · UI E2E · 성능 · 보안 점검 리포트

## P7 · 문서·튜토리얼·파일럿 검증 마감

- 정본: [.planning/phases/07-docs-pilot-validation/](../../../../.planning/phases/07-docs-pilot-validation/)
- 대상: 모듈 집단 1 출시 자격 선언 (23/23)
- 주 추진 영역 (ADR-0001 정본): 사용자 가치 G5-1 ~ G5-3 + 전 영역 잔여 GREEN
- 대표 산출물: 시나리오·매뉴얼 현행화 · 파일럿 검증 자료 · M7 선언

## 작업 흐름 × 모듈 집단 영향도

<!-- status-auto-embed:matrix -->
| 작업 흐름 \ 집단 | W1 (12) | W2 (13) | W3 (14) | W4 (8) |
|---|---|---|---|---|
| P1 | 54/72 | 59/78 | 57/84 | 32/48 |
| P2 | 10/24 | 7/26 | 8/28 | 5/16 |
| P3 | 5/12 | 9/13 | 4/14 | 3/8 |
| P4 | 0/12 | 0/13 | 0/14 | 0/8 |
| P5 | 48/72 | 52/78 | 56/84 | 32/48 |
| P6 | 0/48 | 0/52 | 0/56 | 0/32 |
| P7 | 0/36 | 0/39 | 0/42 | 0/24 |

_셀 = 해당 Phase 게이트 × 해당 Wave 모듈의 통과/대상. 출처: scripts/audit/commercial_readiness.py GATE_PHASE × WAVES_BY_MODULE._
<!-- /status-auto-embed:matrix -->

## 작업 흐름이 끝난 뒤의 모듈 집단 확산

작업 흐름 1~7 이 **v1.0 파일럿 출시 (M7)** 를 만들고 나면, 이후는 모듈 집단 확산 (M8~M10) 이 주도한다. 확산 규칙은 [../matrix.md](../matrix.md) §6 참조.
