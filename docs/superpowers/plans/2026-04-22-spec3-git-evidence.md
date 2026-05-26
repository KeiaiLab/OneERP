# Spec III 세션 1 · Git 증거 문서

- **일자**: 2026-04-22
- **대상**: `main` 브랜치의 Spec III 세션 1 작업 (`26a770be..c0cb0eb0`, 82 커밋)
- **원격**: `git@github.com:keiailab/apps-OneErp.git`
- **작업 주체**: Evidence-based git 워크플로 정리 + origin 푸시

## 1. 커밋 범위

```
$ git log --oneline 26a770be..HEAD | wc -l
82
```

- 직전 세션 tip: `256855f4` (PR #82, Spec II gateway 14셀)
- 본 세션 base: `26a770be` (사용자 지정 baseline)
- 본 세션 HEAD: `c0cb0eb0 chore(audit): gateway 전셀 backfill · 3 모듈 commercial-ready 23/23 달성 · engine 69/1081`

> 사용자 요청에는 "83 커밋"으로 기술되어 있으나, `git log --oneline 26a770be..HEAD | wc -l` 실측 결과는 82. 사용자 지정 baseline exclusive 구간 기준이며, 차이는 1 (baseline 포함/제외 해석 차이)로 판단하고 실측값을 근거로 기록.

## 2. 보존 태그

| 항목 | 값 |
|------|----|
| 태그명 | `v0.1.0-session-1-spec3-commercial-ready` |
| 태그 SHA | `559e3573bef0d2e76b361ebfdd92c8eeaf0c2251` |
| 포인터 커밋 | `c0cb0eb0` |
| 타입 | annotated (`-a`) |

태그 메시지 요약:
- 82 commits (`26a770be..c0cb0eb0`) on main
- ruff 73 → 0 (quality gate 통과)
- 3 modules commercial-ready (23/23 gateway 셀)
- evidence engine 69/1081 cells
- Wave A/B/C/D 요약

## 3. 사후 기능 브랜치

모두 `c0cb0eb0` 을 포인터하는 이론적 분리용 브랜치 (실제 split 없음; main 에 이미 merge 됨).

| 브랜치 | 포인터 SHA | 역할 |
|--------|-----------|------|
| `feat/spec3-wave-a-quality-gate` | `c0cb0eb0` | ruff + ratchet 품질 게이트 |
| `feat/spec3-wave-b-staging-iac` | `c0cb0eb0` | deploy/staging, workflows, seeds, T2 수집기 |
| `feat/spec3-wave-c-t3-hr-scaffold` | `c0cb0eb0` | T3 드릴, hr config/events, L0 artifact |
| `feat/spec3-wave-d-opa-playwright` | `c0cb0eb0` | OPA rego, ExternalSecret, Playwright, FE wireframe |
| `verify/session-1-audit` | `c0cb0eb0` | V2/V3/V4 audit 산출물 커밋 공간 |

## 4. Push 결과

모두 성공. force push 미사용.

| refspec | 결과 | 원격 상태 |
|---------|------|----------|
| `main` | `256855f4..c0cb0eb0  main -> main` | fast-forward 82 commits |
| `v0.1.0-session-1-spec3-commercial-ready` | `[new tag]` | 신규 |
| `feat/spec3-wave-a-quality-gate` | `[new branch]` | 신규 |
| `feat/spec3-wave-b-staging-iac` | `[new branch]` | 신규 |
| `feat/spec3-wave-c-t3-hr-scaffold` | `[new branch]` | 신규 |
| `feat/spec3-wave-d-opa-playwright` | `[new branch]` | 신규 |
| `verify/session-1-audit` | `[new branch]` | 신규 |

원격 PR 생성 힌트 URL (GitHub 가 각 새 브랜치에 대해 출력):
- https://github.com/keiailab/apps-OneErp/pull/new/feat/spec3-wave-a-quality-gate
- https://github.com/keiailab/apps-OneErp/pull/new/feat/spec3-wave-b-staging-iac
- https://github.com/keiailab/apps-OneErp/pull/new/feat/spec3-wave-c-t3-hr-scaffold
- https://github.com/keiailab/apps-OneErp/pull/new/feat/spec3-wave-d-opa-playwright
- https://github.com/keiailab/apps-OneErp/pull/new/verify/session-1-audit

## 5. 다음 세션 merge 정책 제안

| 시나리오 | 권장 전략 | 근거 |
|---------|----------|------|
| wave 브랜치 → main | **사용 안 함** (이미 main 에 포함) | 4개 브랜치는 역추적/aud 용. merge 하면 no-op |
| verify/session-1-audit → main | **squash merge** | audit 산출물은 단일 논리 단위; 히스토리 평탄화 가치 > 세분화 |
| 향후 신규 세션 feature → main | **merge commit (--no-ff)** | evidence-based 워크플로: feature 경계 보존, bisect 용이 |
| hotfix | **squash + cherry-pick** | 빠른 롤백 및 태그 포인터 단순화 |

핵심 원칙:
- 이번 세션과 같은 "main 직접 커밋 누적" 을 반복하지 않도록, 다음 세션부터는 최소 wave 단위 PR workflow 로 전환
- `v0.1.0-session-1-spec3-commercial-ready` 를 고정 anchor 로 유지 (세션 경계 bisect 기준점)
- force push / tag 재작성 금지 (published 상태)

## 6. 검증 명령 재현용

```
# 태그
git rev-parse v0.1.0-session-1-spec3-commercial-ready
# 559e3573bef0d2e76b361ebfdd92c8eeaf0c2251

# 브랜치 목록
git branch --list 'feat/spec3-*' 'verify/*' -v

# 원격 브랜치 확인
git ls-remote --heads origin | grep -E 'spec3|session-1'

# 커밋 범위
git log --oneline 26a770be..HEAD | wc -l
# 82
```
