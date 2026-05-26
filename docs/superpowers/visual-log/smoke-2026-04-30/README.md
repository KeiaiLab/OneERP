# Smoke 시나리오 — oe-feature-pipeliner 첫 통합 호출 (T11)

## 목적

T1~T10에서 만든 `oe-feature-pipeliner` + 매트릭스 + 검증 인프라가 *실제 호출 시*
4 Stage 모두 통과 + verdict.PASS + next_action=commit+ship+deploy를 반환하는지 확인.

## 본 세션 (T11) 완료 항목

- 환경 준비:
  - `feat/oe-feature-pipeliner-agent-team` worktree 검증 인프라 6 모듈 + 매트릭스 + ADR + AGENTS.md 갱신 *완료*
  - 누적 41 단위 테스트 PASS (검증 인프라 자체 동작 확인) — 재확인: `PYTHONPATH=. /Users/phil/WorkSpace/apps/OneErp/.venv/bin/pytest tests/unit/agents/ -v`
- 절차 가이드: 본 README의 "## 후속 세션 수동 절차"

## 후속 세션 수동 절차 (사용자 진행)

본 PR 머지 후 별도 세션에서:

### 1. smoke 브랜치 + 작은 BE+FE 변경

```bash
git checkout main
git checkout -b smoke/oe-feature-pipeliner-2026-04-30
```

다음 변경 (작은 단위):
- BE: `services/buying/app/routers/health.py`에 `/health/version` 엔드포인트 추가 (예시 — 다른 서비스 적용 시 동일 패턴)
  - 응답 schema: `{"version": str, "git_sha": str}` (Pydantic 신규 → ADR 트리거 예상)
- FE: `web/app/admin/health/page.tsx`에 version 카드 추가

### 2. pipeliner 호출

Claude Code 메인 스레드(parent agent)에서 다음 sub-Task 호출 — 사용자가 직접 입력하지 말고, Claude에게 "아래 Task를 호출해 줘"라고 요청:
```
Task(subagent_type="oe-feature-pipeliner",
     prompt="health/version 엔드포인트 + admin 화면 카드 추가 — smoke 시나리오. plan 메타 없음, 사용자 직접 호출(dispatcher: user).")
```

### 3. verdict 받기 + 본 README에 추가 기입

verdict JSON을 받아 본 README의 "## 실행 결과" 섹션에 붙여넣음. 기대값:
- `verdict: PASS`
- `stages.be / typebridge / fe / visual` 모두 `skipped: false`, 결과 OK
- `ground_truth.grep_mismatch: 0`
- `adr_triggered: true` (Pydantic schema 신규)
- `next_action: commit+ship+deploy`

### 4. 검증 + 정리

- ADR sub-Task가 작성한 ADR 파일이 `docs/governance/adr/`에 추가됐는지 확인
- visual-log/smoke-2026-04-30/에 before/after PNG 존재 확인
- ground_truth.grep_mismatch == 0 확인

스모크 변경 자체는 *되돌리거나 버림* (smoke 브랜치 폐기) — 본 작업은 인프라 검증이 목적.

```bash
git checkout main
git branch -D smoke/oe-feature-pipeliner-2026-04-30
```

### 5. smoke 결과 commit (visual-log만)

main 브랜치로 돌아온 뒤(Step 4의 `git checkout main` 다음) 본 README에 verdict 기입 후 commit:

```bash
LEFTHOOK=0 git add docs/superpowers/visual-log/smoke-2026-04-30/
LEFTHOOK=0 git commit -m "docs(smoke): pipeliner 첫 통합 호출 결과 [skip-hooks]"
```

## 실행 결과

(후속 세션에서 verdict JSON 붙여넣기 — 현재 미실행)

## 한계

본 세션에서는 *완전 smoke 자동화 불가*:
- auto-cycle Phase 3 dispatcher 측 변경(`~/.claude/skills/auto-cycle/SKILL.md` 경로 패턴 감지
  + plan 메타 평가 + marker 주입)이 *별도 후속*
- worktree에서 `core/`/`web/` 서브모듈 미초기화 — uv workspace 빌드 실패

따라서 본 task는 *환경 준비 + 절차 문서*까지로 제한.
실제 호출과 verdict 기록은 후속 세션의 수동 단계.
