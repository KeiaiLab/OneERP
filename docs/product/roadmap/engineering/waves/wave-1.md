---
owner: Wave 1 Owner
last_updated: 2026-04-16
stale_after_days: 30
audience: engineering
wave: 1
module_count: 12
---

# 모듈 집단 1 — 재무·운영 핵심 (12 모듈)

> 가장 먼저 출시 자격(23/23 기준 통과)을 얻는 1차 집단. 매출 영향·의존성·리스크·빈도 4 점수 기반으로 분류되었다.

## 1. 포함 모듈

<!-- wave-module-table:1 -->
_Wave 1 의 12 모듈. 정본: ADR-0012 §6. 자동 렌더._

| 모듈 | 현재 라벨 | 통과 | 실패 | 구현 | /23 |
|---|---|---|---|---|---|
| `gateway` | **alpha** | 10 | 13 | 23 | /23 |
| `directory` | **alpha** | 6 | 17 | 23 | /23 |
| `accounting` | **alpha** | 11 | 12 | 23 | /23 |
| `hr` | **alpha** | 10 | 13 | 23 | /23 |
| `payroll` | **alpha** | 11 | 12 | 23 | /23 |
| `selling` | **alpha** | 10 | 13 | 23 | /23 |
| `buying` | **alpha** | 10 | 13 | 23 | /23 |
| `stock` | **alpha** | 11 | 12 | 23 | /23 |
| `expenses` | **alpha** | 10 | 13 | 23 | /23 |
| `projects` | **alpha** | 11 | 12 | 23 | /23 |
| `crm` | **alpha** | 10 | 13 | 23 | /23 |
| `portal` | **alpha** | 7 | 16 | 23 | /23 |
<!-- /wave-module-table:1 -->

정본: [ADR-0012 §6](../../../../governance/adr/0012-commercialization-wave-mapping.md) · 각 모듈 ERD는 [docs/generated/INDEX.md](../../../../generated/INDEX.md) 참조.

## 2. 진입 / 완료 조건

- 진입: 이전 집단이 없으므로 개시 조건은 "작업 흐름 1 안정화 착수"
- 완료: 12 모듈 중 **80% 이상이 23/23 기준 통과** → 다음 집단 실행 자원 전환 승인
- 세부 조건은 [ADR-0012 §6](../../../../governance/adr/0012-commercialization-wave-mapping.md) 참조

## 3. 진행률 임베드

<!-- status-auto-embed:wave-1-progress -->
- 집단 1: 117 / 276 기준 통과 (42.4%)
- 모듈 수: 12
- 최고 통과 모듈: accounting (11/23)
<!-- /status-auto-embed:wave-1-progress -->

## 4. 의존 작업 흐름

이 집단이 활성인 기간에 **함께 진행되는** 작업 흐름:

| 작업 흐름 | 주 영향 | 상태 |
|---|---|---|
| [P1 이벤트 체인](../phase-timeline.md#p1--이벤트-체인-안정화) | 전 모듈 공통 통합 기준 #1~#3 | _대기_ |
| [P2 핵심 운영 E2E](../phase-timeline.md#p2--핵심-운영-e2e-완성) | 기능 기준 #1~#5 | _대기_ |
| [P3 협업·결재 UI](../phase-timeline.md#p3--협업영업-흐름--결재-ui) | 기능 기준 #4~#5 (Groupware 교집합) | _대기_ |
| [P4 대시보드·보고서](../phase-timeline.md#p4--대시보드보고서-사용자-출력) | 기능 기준 #5 + 배포 #1 | _대기_ |
| [P5 운영 인프라](../phase-timeline.md#p5--파일럿-운영-인프라-마감) | 배포 #1~#3 + 운영 #1~#3 | _대기_ |
| [P6 QA·성능·보안](../phase-timeline.md#p6--통합-qa성능보안-검증) | 운영 #4~#5 + 보안 #1~#7 | _대기_ |
| [P7 문서·파일럿](../phase-timeline.md#p7--문서튜토리얼파일럿-검증-마감) | 잔여 · GREEN 확인 · M7 선언 | _대기_ |

## 5. 주요 위험 Top 3

<!-- status-auto-embed:wave-1-risks -->
_위험 등록부 태그 `wave:N` 필터 결과. (데이터 소스 연결 대기)_
<!-- /status-auto-embed:wave-1-risks -->

## 6. 완료 모습 (What done looks like)

로컬에서 이 집단의 commercial-ready 상태를 재현하려면:

```bash
make smoke                                                # 로컬 환경 검증
uv run pytest tests/e2e -m "wave-1" -q                   # Wave 1 E2E 시나리오
uv run python3 scripts/audit/wave_entry_check.py \
    --wave 1 --assert commercial-ready                   # 23/23 기준 통과 검증
uv run python3 scripts/audit/commercial_readiness.py \
    --wave 1 --format summary                            # 집단 리포트
```

모두 exit 0 이면 이 집단은 출시 자격을 충족한 것이다.

## 7. 참조 블록

- [ADR-0001 23 품질 기준](../../../../governance/adr/0001-commercial-grade-definition.md)
- [ADR-0002 단일 활성 집단 원칙](../../../../governance/adr/0002-commercialization-waves.md)
- [ADR-0012 모듈 분류 근거](../../../../governance/adr/0012-commercialization-wave-mapping.md)
- [ADR-0014 Plane 분해](../../../../governance/adr/0014-runtime-plane-decomposition.md)
- [자동 생성 모듈 ERD 인덱스](../../../../generated/INDEX.md)
- [v1.0 프로그램](../../../../../.planning/program/milestones/v1.0-program.md)
