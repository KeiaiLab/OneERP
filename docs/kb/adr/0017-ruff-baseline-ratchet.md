---
title: ADR-0017 · ruff baseline 하향 + ratchet CI 도입
date: 2026-04-22
status: accepted
tags: [quality, ci, ruff, commercial-grade-v2]
---

# ADR-0017 · ruff baseline 하향 + ratchet CI 도입

## Context

Commercial Grade v2 Spec II 종료 시점 ruff error count가 73까지 증가. 신규 코드가 baseline을 올리고 있는 상태로, Spec III 수평 확장 직전에 베이스라인을 하향하고 증가 방향을 구조적으로 차단할 필요.

## Decision

1. **Wave A 하향**: 73 → 30 (-43) 달성.
   - per-file-ignores 보강(tests/security·scripts 정당화) → -4
   - `ruff check --fix` (safe) + 포매팅 정렬 → -7
   - `ruff check --fix --unsafe-fixes` (TC003 TYPE_CHECKING 블록화, PERF401, RUF001-003) → -32
2. **ratchet CI 도입**: `.github/workflows/ruff-ratchet.yml` — 모든 PR에서 ruff error count가 origin/main 대비 증가하면 fail.
3. **ratchet 예외**: ruff 버전 업그레이드 PR은 `[ratchet-bump]` 라벨로 수동 승인.
4. **Wave D 종료 시 floor 합의**: option F (≤ 5 with ADR 근거) 또는 option 0 (전수 수정) 중 택1. ADR-0018 박제.

## Consequences

- 신규 PR은 ruff error를 줄이거나 같게만 머지 가능
- Spec III 신규 코드(accounting/hr)가 baseline을 올리지 못함 — 구조적 가드
- ratchet 실패 시 작업자는 신규 코드에 `noqa` 대신 기존 error 1건을 먼저 정리

## Evidence

- Wave A 시작: Found 73 errors (2026-04-22 정찰)
- Wave A 종료: Found 30 errors (커밋 `0fddd20d`)
- 변경 규칙 Top: TC003 29→0, PERF401 4→0, RUF001-003 7→0
- 잔여 30: ERA001 8, FBT 6, A002 4, PERF401 4, RUF 7, SLF 1
- count 스크립트: `scripts/ci/count-ruff-errors.sh`
- ratchet workflow: `.github/workflows/ruff-ratchet.yml`

## Related

- ADR-0018 (예정): Wave D floor 확정 · Spec III/II.5 완료 선언
- 설계: `docs/superpowers/specs/2026-04-22-spec3-staging-quality-design.md`
- 플랜: `docs/superpowers/plans/2026-04-22-spec3-staging-quality.md`
