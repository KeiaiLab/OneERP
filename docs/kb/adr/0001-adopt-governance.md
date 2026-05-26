# ADR-0001: 글로벌 v3.0 거버넌스 채택 (OneErp)

- Date: 2026-04-28
- Status: Accepted
- Authors: @phil
- Tags: governance, ai-ops, multi-project, reverse-promotion

## Context

본 repo의 ADR/incident KB 패턴(`docs/governance/adr/`, `artifacts/verification/session-*/`)은 7 repo 중 가장 성숙한 모델로, 글로벌 standards의 *역승격(reverse promotion) 출처*가 되었다. 즉 본 repo의 패턴이 글로벌 표준이 되었으므로, 본 repo도 그 표준에 *공식 합류*해야 일관성이 닫힌다.

OneErp의 ralph-loop 자동화 루프가 빈번하게 commit을 만들기 때문에 hook 우회 메커니즘(`LEFTHOOK=0` env, `[skip-hooks]` 트레일러)이 *명시적으로 설계*되어야 한다.

## Decision

본 repo의 `CLAUDE.md`가 글로벌 진입점을 import한다. AGENTS.md는 *프로젝트 고유 작업 규칙*(0단계 인벤토리, FE 시각 검증 등)을 유지하며, 글로벌 표준과 *보완 관계*로 작동한다.

추가 도입:
- `docs/kb/adr/` 신설 — 본 repo는 기존 `docs/governance/adr/`와 *이중 운영* (역사 보존)
- `lefthook.yml`에 ralph-loop 우회 명시 (`[skip-hooks]` 트레일러)
- `artifacts/` gitignore 가드 (lefthook이 SHADOW-WARN)

## Consequences

### 긍정
- 본 repo의 ADR 패턴이 *글로벌 표준*으로 공식 인정 — 향후 다른 repo도 동일 패턴 적용
- ralph-loop 자가수정이 글로벌 §self-repair 정책으로 *공식 인정* (검증 의무 + 금지 영역 명시)
- FE visual-dual-loop 스킬이 standards/checklist.md §3 PR 체크와 정합

### 부정 / 트레이드오프
- `docs/governance/adr/` ↔ `docs/kb/adr/` 두 경로 공존 — 신규 ADR은 어디에 작성할지 컨벤션 필요
- ralph-loop의 `[skip-hooks]` 우회 회수가 메트릭에 누적 → 남용 시 ADR 작성

### 후속 작업
- [ ] AI-001: ADR 경로 통일 결정 — `docs/governance/adr/` → `docs/kb/adr/` 마이그레이션 또는 별도 RFC
- [ ] AI-002: ralph-loop의 자가수정 회수 월간 추적 (`scripts/self-repair-stats`)
- [ ] AI-003: 0단계 인벤토리 자동 검증 스크립트 도입

## Alternatives Considered

| 대안 | 거절 사유 |
|------|----------|
| OneErp 기존 패턴만 유지 (글로벌 import X) | 다른 6 repo와의 일관성 결손 |
| 글로벌 표준으로 강제 통일 (OneErp 기존 패턴 폐기) | 검증된 패턴의 가치 손실 |
| `docs/governance/adr/`만 사용 (글로벌 표준 무시) | 신규 repo와 호환성 깨짐 |

## References

- 글로벌 RFC-0001: 본 repo의 패턴이 §3 Detailed Design의 ADR/incident KB 모델 근거
- 기존 ADR: `docs/governance/adr/0013-commercial-gate-drill-evidence.md`, `0016-commercial-grade-v2-evidence.md`
- ralph-loop: `RALPH-LOOP-PROMPT.md`
