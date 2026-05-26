---
description: Commercial Grade v2 증거 엔진 — wave 기반 3자원 병렬 감사·리팩토링
argument-hint: <subcommand> [args]
allowed-tools: Read, Bash, TaskCreate, TaskList, TaskGet, TaskUpdate, AskUserQuestion, Task, Grep, Glob
---

# /commercial-engine {{args}}

> **Spec**: `docs/superpowers/specs/2026-04-22-commercial-grade-v2-triple-resource-design.md`
> **Plan**: `docs/superpowers/plans/2026-04-22-commercial-grade-v2-engine.md`
> **Entry**: `ce-planner` (singleton) 이 subcommand 분기 조율.

## 실행 절차

1. **ce-planner dispatch** — `$ARGUMENTS` 를 파싱해 subcommand 결정
2. **Subcommand 분기** — 아래 표 참조
3. **공통 출력** — 작업 요약 + 다음 권장 호출

## Subcommand

| subcommand | 부작용 | 구현 |
|---|---|---|
| `status` | 없음 (read-only) | `uv run python3 -m scripts.audit.commercial_readiness --format text` |
| `plan [--module M] [--max N]` | 없음 | `scripts/engine/wave_planner.plan_wave()` 로 wave plan 생성·표시. 실행 없음. |
| `wave [--module M] [--max N] [--dry-run]` | 있음 (파일·커밋) | 7단계 사이클 — 아래 § Wave 절차 |
| `audit [--verify-evidence]` | status 갱신 | `--verify-evidence` 시 ce-reviewer 가 20% replay |
| `reset-v1 --confirm` | 1회 · 대규모 | `uv run python3 -m scripts.engine.migration.reset_v1 --confirm` |
| `staging <module> <gate>` | T3 증거 생성 | 사용자 승인 필수 · 단일 게이트만 |
| `replay <sha>` | 없음 | `uv run python3 -m scripts.engine.replay --sha <sha>` |
| `escalate` | HANDOFF.md 작성 | 현 세션 중단 · 인수인계 작성 |

## Wave 절차 (7 단계)

1. **Preflight** — ce-planner 가 11 블로커 스캔 (시크릿/삭제/과금/법적/force-push/3회실패/품질회귀/revert진동/라벨하락/push실패/compose실패)
2. **Plan** — `commercial-status.json` 읽고 `scripts/engine/wave_planner.py` 로 wave 구성
3. **User Approval** — `AskUserQuestion` 으로 plan 제시 → 승인/거부/재계획
4. **Dispatch** — ce-artisan × N + ce-scribe × M + ce-executor × K 병렬 (N+M ≤ 5, K ≤ 8)
5. **Review** — ce-reviewer (싱글톤) 교차 검증·회귀 감지·20% replay → verdict 결정
6. **Audit** — `python3 -m scripts.audit.commercial_readiness --format json` 재실행 → delta·회귀 확인
7. **Commit**
   - 7a feature: `git commit -m "feat(<scope>): G<x>-<y> PASS 달성 · <module>"`
   - 7b progress: `git commit -m "chore(progress): wave <id> 기록 (+<delta>/1081)"`

## 주의사항

- `wave` 는 반드시 `AskUserQuestion` 승인 후 실행
- T3 staging 작업은 `staging` subcommand 로만 (wave 가 자동 T3 실행 금지)
- 11 블로커 감지 시 즉시 중단 · 사용자에게 보고
- 커밋 규약: `Evidence-SHA` · `Wave-ID` 필드 (Spec §9.3)
