---
role: design
status: approved
last_updated: 2026-04-16
audience: engineering, ai-agent
target_milestone: M7 (v1.0 파일럿 출시 기준선)
approach: Gate-Walker (Approach B)
autonomy: Full Autopilot with standard safety perimeter
cross_refs:
  skill: .claude/skills/ralph-loop/SKILL.md
  plugin: /ralph-loop:ralph-loop
  roadmap: .planning/ROADMAP.md
  requirements: .planning/REQUIREMENTS.md
  release_criteria: .planning/program/releases/RELEASE-CRITERIA.md
  v1_program: .planning/program/milestones/v1.0-program.md
  quality_baseline: docs/governance/adr/0001-commercial-grade-definition.md
  wave_mapping: docs/governance/adr/0012-commercialization-wave-mapping.md
  audit_script: scripts/audit/commercial_readiness.py
  roadmap_gates: scripts/roadmap/
  gate_catalog: docs/product/roadmap/gates/README.md
  translation: docs/product/roadmap/translation.md
---

# Ralph-Loop to GTM (M7) 설계 문서

> OneERP v1.0 파일럿 출시 기준선(M7)까지 Ralph-Loop을 Full Autopilot으로 가동하기 위한 단일 설계 문서.
> 이 문서가 승인되면 `docs/superpowers/plans/2026-04-16-ralph-loop-to-gtm.md` 구현 계획으로 이어진다.

## § 0. 이 설계가 존재하는 이유

OneERP는 이미 `.planning/phases/01~07/*-PLAN.md`로 Phase 1~7 실행 설계가 완성되어 있고,
`scripts/audit/commercial_readiness.py`로 47 모듈 × 23 품질 기준 = 1,081 셀의 정량 측정 체계가 구축되어 있다.
부족한 것은 "이 정량 매트릭스를 M7까지 자율 반복 루프로 밀어 올리는 단일 오케스트레이션"이다.

본 문서는 그 오케스트레이션을 **하나의 Ralph-Loop 세션으로 설계**한다. OneERP 전용
`.claude/skills/ralph-loop/SKILL.md` 가 요구하는 두 제어 파일 — `RALPH-LOOP-PROMPT.md`,
`PROGRESS.md` — 의 스펙과 동작 규약을 본 설계가 결정한다.

---

## § 1. 의사결정 요약 (Brainstorming 결과)

본 설계는 2026-04-16 브레인스토밍 세션에서 사용자가 선택한 아래 6개 결정 위에 구성된다.

| # | 결정 항목 | 선택 | 함의 |
|---|---|---|---|
| Q1 | GTM 범위 | **A**: M7 = v1.0 파일럿 출시 기준선 | Wave 1 모듈 12개 × 23 게이트 전수 PASS 가 완료 조건. 파일럿 고객 확보나 영업 활동은 범위 외. |
| Q2 | 자율성 경계 | **A**: Full Autopilot | Phase 경계 체크포인트 없음. 루프가 M7 선언까지 무인 반복. 단 하드 블로커 발동 시 자동 정지. |
| Q3 | 안전 경계 | **B**: 표준 | 5 하드 블로커(v2.3 규약) + 6 안티진동 감지 = 11 정지 조건. |
| Q4 | 루프 시작 상태 | **A**: Clean state 후 시작 | 워킹트리 9 modified + 1 untracked + 미push 26 커밋 + 시각 이중 루프 트랙 모두 정리 후 기동. |
| Q5 | Cleanup 주체 | **A**: Claude 전담 | 시각 이중 루프 Task 4~6 완결 포함. Task 5에서 chrome-devtools-mcp 사용자 확인 1회 발생 가능. |
| 접근법 | 반복 축 | **B**: Gate-Walker | 276 셀(Wave 1 × 23) 매트릭스 직접 드라이브. Phase-Walker 대신. |

추가 확정된 기본값:
- 부트스트랩 층 5 항목 (FL1~FL4 E2E + event-contract drift): 채택
- 영역 우선순위: `G1(기능) < G3(보안) < G4(운영) < G5(문서) < G2(성능)`
- 모듈 우선순위: ADR-0012 Wave 1 실측 순서 — `scripts/audit/commercial_readiness.py::WAVES_BY_MODULE[1]` 기준 12 모듈: `gateway, directory, accounting, hr, payroll, selling, buying, stock, expenses, projects, crm, portal` (manufacturing 은 Wave 2 이므로 제외. directory 가 Wave 1 에 포함됨)
- G4-3 backup / G4-4 rollback PASS 판정: **정적 증거(문서 + dry-run 로그)로 인정** — 실측 리허설은 루프 외부 책임
- `--max-iterations 999`: 스킬 규약 고정
- HANDOFF.md 포맷 현행 유지

---

## § 2. 아키텍처 & 제어 파일

### 2.1 실행 Envelope

```bash
# Pre-loop cleanup 완료 · clean main 상태에서 1회 기동
/ralph-loop:ralph-loop "$(cat RALPH-LOOP-PROMPT.md)" \
  --max-iterations 999 \
  --completion-promise "ONEERP_COMPLETE"
```

`.claude/skills/ralph-loop/SKILL.md` 가 이 시그니처를 요구하므로 envelope 자체는 변경 없다.
설계의 실질은 `RALPH-LOOP-PROMPT.md` 의 내용이다.

### 2.2 제어 파일 5종

| 파일 | 경로 | 역할 | 수명 주기 |
|---|---|---|---|
| RALPH-LOOP-PROMPT.md | 레포 루트 | 루프의 "OS 커널". 매 iter 동일 프롬프트. | Pre-loop(나)이 생성 → 루프 중 불변 |
| PROGRESS.md | 레포 루트 | 이터레이션 로그. 타겟 셀/커밋/delta/소요. | Pre-loop(나)가 초기화 → 매 iter 루프가 append |
| .claude/ralph-loop.local.md | 레포 | 세션 상태 (iteration 번호, started_at, heartbeat). | 플러그인 자체 관리 |
| docs/generated/commercial-status.json | 생성 | 276 셀 진리상태 SoT. | 매 iter `commercial_readiness.py --format json --write` 재생성 |
| HANDOFF.md | 레포 루트 | 에스컬레이션 저널. 하드 블로커 발동 시 덮어씀. | 기존 파일(2026-04-13) → cleanup 단계 6에서 갱신 → 블로커 시 덮어씀 |

### 2.3 데이터 흐름 (한 iter)

```
iteration N 시작
     │
     ▼  ① commercial_readiness.py --format json --wave 1 --write
     ▼  ② 안전 경계 11 블로커 체크 → hit 시 HANDOFF.md 기록 후 정지
     ▼  ③ 종료 판정 (276/276 + verify-roadmap + 라벨 + 품질 게이트) → true 시 ONEERP_COMPLETE
     ▼  ④ 타겟 셀 선택 (§3.2 우선순위 규칙)
     ▼  ⑤ 게이트 함수 역산 → 요구 산출물 식별
     ▼  ⑥ TDD: failing test → 구현 → green
     ▼  ⑦ 로컬 품질 게이트 (대상 영역)
     ▼  ⑧ atomic commit (한국어 메시지)
     ▼  ⑨ audit 재실행 · delta 검증 (delta < 1 이면 iter 중단 · 역산 오류)
     ▼  ⑩ PROGRESS.md append
     └─► iteration N+1
```

### 2.4 PROGRESS.md 포맷

```markdown
# OneERP Ralph-Loop PROGRESS

- 시작: 2026-04-16T14:XX:XXZ
- 목표: ONEERP_COMPLETE = Wave 1 × 23/23 전수 PASS
- 현재 진행률: <passed>/276 · <percent>%
- 최근 갱신: <ISO8601>

## Iteration Log

| iter | ts | target | action | commit | delta | duration |
|---|---|---|---|---|---|---|
| 1 | 2026-04-16T15:00 | accounting × G1-2 | docs/api/accounting/openapi.yaml 생성 | a1b2c3d | +1 | 18min |
```

`delta` 열은 게이트 셀 진척 추적(+N: 통과 증가, -N: 회귀)에 사용한다.
모듈 라벨 하락 감지(블로커 #9)에 연결되며, 품질 게이트 회귀 수(블로커 #7)는
별도로 `ruff\|ty\|biome` exit 차이로 측정한다 (delta 열과 혼동 금지).

---

## § 3. 이터레이션 알고리즘 & 게이트 선택

### 3.1 의사 코드 (RALPH-LOOP-PROMPT.md 의 구현 지시)

```python
def iteration(N):
    # 1) 상태 로드
    status = audit_wave1_json()  # commercial_readiness.py --wave 1 --format json
    progress = read("PROGRESS.md")
    bootstrap_green = check_bootstrap_green()

    # 2) 안전 경계
    if hard_blocker_detected(progress, status): escalate_and_stop()

    # 3) 종료 판정
    if all_four_checks_green(status): emit("ONEERP_COMPLETE"); return

    # 4) 타겟 선택
    target = select_next_cell(status, bootstrap_green)

    # 5) 산출물 역산
    required = introspect_requirements(target)

    # 6) TDD
    write_failing_test(target)
    assert_test_fails()
    implement(required)
    assert_test_passes()

    # 7) 로컬 품질 게이트 (대상 영역만)
    verify_local_quality_gates(target.area)

    # 8) Atomic commit
    commit(korean_message(target))

    # 9) Audit 재실행 · delta 검증
    new_status = audit_wave1_json()
    if new_status.passed(target) != status.passed(target) + 1:
        abort("게이트가 실제로 통과하지 않음")
    if regression_count(status, new_status) > 0:
        halt_and_escalate()

    # 10) PROGRESS.md append
    append_iter_row(N, target, commit_hash, delta=+1, duration)
```

### 3.2 타겟 셀 선택 규칙

```
1. 부트스트랩 미완료 → 부트스트랩 층에서만 선택
2. 부트스트랩 GREEN 이후:
   a. 선행 조건 미충족 게이트 필터 제외 (§3.4)
   b. 남은 셀 정렬:
      (i)  영역 순위: G1 < G3 < G4 < G5 < G2
      (ii) 모듈 순위: ADR-0012 Wave 1 순서
      (iii) 게이트 번호 오름차순
3. 선택된 셀을 타겟으로 반환
```

### 3.3 부트스트랩 층 (5 항목)

Phase 1 이벤트 체인 등가. 모든 G1-3/G1-4/G2-* 게이트 선택은 이 층이 GREEN 이 되어야만 개방된다.

| # | 게이트/테스트 | PASS 조건 |
|---|---|---|
| 1 | event-contract drift | `bash scripts/ci/check_event_contract_drift.sh` exit 0 |
| 2 | FL1 Order-to-Cash E2E | `uv run pytest tests/e2e/test_order_to_cash.py` GREEN |
| 3 | FL2 Procure-to-Pay E2E | `uv run pytest tests/e2e/test_procure_to_pay.py` GREEN |
| 4 | FL3 Payroll → Accounting E2E | `uv run pytest tests/e2e/test_payroll_accounting.py` GREEN |
| 5 | FL4 Manufacture → Stock E2E | `uv run pytest tests/e2e/test_manufacturing_flow.py` GREEN |

`check_bootstrap_green()` = 모두 GREEN 이면 True.
이 값이 False 인 동안 루프는 이 5개 중 FAIL 인 것을 iter 단위로 집중 공략한다.
`.planning/phases/01-event-chain-stabilization/01-01-PLAN.md` 와
`.planning/phases/02-core-ops-e2e/02-01-PLAN.md` Task 3 을 참조 설계서로 활용.

### 3.4 선행 조건 그래프

```
G1-1 ERD ──┐
           ├─► G1-2 OpenAPI ─┬─► G1-5 UI ─┐
           │                  │            ├─► G5-1 매뉴얼 ─┬─► G5-3 UAT
bootstrap ─┼─► G1-3 통합     ├─► G1-4 단위│                │
           │                  │            │                │
           │                  │            └─► G5-2 튜토리얼 ─┘
           │                  │
           │                  ├─► G2-2 load_test
           │                  └─► G2-3 regression
           │
           ├─► G3-1 auth ─► G3-2 권한 ─► G3-3 multitenancy ─► G3-4 감사
           │                                                  └─► G3-5 deps
           │
           └─► G4-1 관측 ─► G4-2 runbook ─► G4-3 backup ─► G4-4 rollback ─► G4-5 oncall

G2-1 SLO, G2-4 chaos, G2-5 i18n: G1-1~G1-5 + G4-1 PASS 이후에만 열림.
```

### 3.5 이터레이션 시간 예산 (이론값)

| 게이트 클래스 | 추정 iter 시간 | × 모듈 | 소계 |
|---|---|---|---|
| G1-1 ERD | 5~15 min | 12 | ≤ 3 h |
| G1-2 OpenAPI | 15~45 min | 12 | ≤ 9 h |
| G1-3 integration | 30~90 min | 12 | ≤ 18 h |
| G1-4 unit ≥90% | 1~3 h | 12 | ≤ 36 h |
| G1-5 UI | 30~120 min | 12 | ≤ 24 h |
| G2-* | 1~4 h | 60 | ≤ 240 h |
| G3-* | 1~3 h | 60 | ≤ 180 h |
| G4-* | 1~4 h | 60 | ≤ 240 h |
| G5-* | 30~90 min | 36 | ≤ 54 h |
| 부트스트랩 | 2~6 h | 5 | ≤ 30 h |
| **합계 (상한)** | | | **≈ 834 h** |

현실 견적: 평균 90 min × 276 = **≈ 414 h (17일 풀가동)**.
`--max-iterations 999` 는 276 셀 × 평균 2회 재시도 여유까지 흡수 가능.

---

## § 4. 종료 판정 & 안전 경계

### 4.1 `ONEERP_COMPLETE` 방출 조건 (4중 체크 AND)

```bash
# 체크 1: Wave 1 × 23 = 276/276 PASS
python3 scripts/audit/commercial_readiness.py --wave 1 --format json \
  | jq '.summary.passed == 276 and .summary.total == 276'

# 체크 2: 로드맵 게이트 4종 GREEN
make verify-roadmap

# 체크 3: Wave 1 모듈 전원 commercial-ready 라벨
python3 scripts/audit/commercial_readiness.py --wave 1 --format json \
  | jq '.modules | all(.label == "commercial-ready")'

# 체크 4: 전체 품질 게이트 로컬 통과
uv run ruff format --check . && uv run ruff check . && uv run ty check .
uv run pytest -m "not integration and not e2e" services/ packages/ tests/unit/
pnpm --filter @oneerp/web lint && pnpm --filter @oneerp/web typecheck && pnpm --filter @oneerp/web build
```

4 체크 모두 exit 0 인 iteration 에서만 `ONEERP_COMPLETE` 출력 허용.
플러그인 규약 "completion-promise 는 statement 가 completely and unequivocally TRUE 일 때만 출력" 준수.

### 4.2 11 하드 블로커

| # | 블로커 | 검출 로직 |
|---|---|---|
| 1 | 시크릿/키/토큰/인증서 필요 | diff에서 `SECRET_KEY\|TOKEN\|PRIVATE_KEY\|.pem\|.key\|.crt` 생성/수정 감지 |
| 2 | 운영 리소스 삭제 | diff에서 `kubectl delete\|helm uninstall\|docker volume rm\|docker image rm\|namespace.*delete` 감지 |
| 3 | 외부 과금 액션 | `boto3\|gcloud compute\|terraform apply` 등 신규 도입 감지 |
| 4 | 라이선스/법적 변경 | `LICENSE\|TERMS\|PRIVACY\|legal/` 경로 수정 감지 |
| 5 | 메인 force push / 태그 삭제 / published amend | `git push --force\|git tag -d\|git commit --amend` 시도 자체 금지 |
| 6 | 동일 verify 커맨드 3회 연속 실패 | PROGRESS.md 최근 3 iter 의 `verify` 필드(문자열 동일) 가 모두 non-zero exit |
| 7 | 품질 게이트 회귀 +10 | ruff/ty/biome 회귀 수 diff > 10 |
| 8 | 커밋 5회 revert/reapply 진동 | `git log --grep=Revert --since=2h` > 5 |
| 9 | 모듈 라벨 하락 | alpha ← beta ← pre-commercial 역주행 감지 |
| 10 | push 실패 / upstream 충돌 | `git push --dry-run origin main` 비 zero exit |
| 11 | compose 기동 3회 실패 | 최근 3 iter 연속 `compose-up.sh` 실패 |

### 4.3 HANDOFF.md 에스컬레이션 포맷

```markdown
# 세션 핸드오프 — Ralph-Loop 자동 정지

작성: <ISO8601>
정지 사유: 블로커 #<N> — <이름>

## 직전 상태
- iteration: <N>
- 마지막 커밋: <hash> — <subject>
- 타겟 셀: <module> × <gate>
- 전체 진행률: <passed>/276 (<percent>%)

## 검출 증거
<raw output 인용>

## 사용자 조치 제안
<블로커별 템플릿>

## 재개 방법
1. 위 조치 완료
2. `git status` clean 확인
3. `.claude/skills/ralph-loop` 재호출 → PROGRESS.md 기반 재개
4. PROGRESS.md 마지막 iter 기준 재시도 또는 다음 셀 이동
```

### 4.4 재개 프로토콜

- 정지 직후: `.claude/ralph-loop.local.md` 에 `status: paused` 마킹
- 재기동: 동일 `/ralph-loop:ralph-loop ...` 명령. 플러그인이 이전 상태 이어받음
- 루프 판단: 타겟 셀 여전히 FAIL → 재시도, PASS → 다음 셀

### 4.5 긴급 수동 중단

`/cancel-ralph` 플러그인 명령. PROGRESS.md 는 현재 상태까지 보존.

---

## § 5. Pre-Loop Cleanup (6 단계)

Clean state 확보까지의 작업 순서. 각 단계는 atomic commit.

| 단계 | 작업 | 검증 |
|---|---|---|
| 1 | 워킹트리 현황 분석 (2026-04-16 세션 시작 기준: `README.md` / `docs/ARCHITECTURE-MAP.md` / `docs/INDEX.md` / `docs/infra/inventory/cicd.md` / `docs/infra/inventory/repo.md` / `docs/infra/ops/rollback.md` / `docs/ops/runbook-service-deploy.md` / `scripts/ci/run.sh` / `tests/e2e/conftest.py` modified, `docs/engineering/architecture/repo-structure-rules.md` untracked, `web` submodule pointer modified) + core/ 서브모듈의 사용자 작업(`tests/fixtures/docs/arch-sample/good.md`, `tests/unit/docs/test_audit_architecture.py` 등) 이 루프와 무관한지 확인 | `git diff --stat`, `git diff <file>` 순회, `git -C core/ status` |
| 2 | 의미 단위 1~3 커밋 분할 | 각 커밋 후 `git status` clean |
| 3 | web/ detached HEAD 해소 (feature branch 복귀) + 미커밋 · untracked 주제별 분할 커밋 + 서브모듈 pointer 갱신 (2026-04-16 실측: 시각 이중 루프 Phase 1~4 + 전파는 이미 완료 상태 · chrome-devtools-mcp 사용자 확인 불필요) | web clean working tree + 부모 레포 web pointer 커밋 반영 |
| 4 | web submodule + 부모 레포 push | `git push --dry-run` 선행 |
| 5 | RALPH-LOOP-PROMPT.md + PROGRESS.md 신규 작성 | 두 파일 존재 + `make verify-roadmap` GREEN |
| 6 | 본 설계 문서 커밋 + HANDOFF.md "Ralph-Loop 대기 중" 상태 | 모든 게이트 GREEN + clean main |

### 5.1 Kickoff 시점 상태 보증

Ralph-loop 기동 직전 다음 모두 true:

```bash
[[ -z "$(git status --porcelain)" ]]
[[ "$(git rev-list --count HEAD..origin/main)" == "0" ]]
[[ "$(git rev-list --count origin/main..HEAD)" == "0" ]]
[[ -f RALPH-LOOP-PROMPT.md ]]
[[ -f PROGRESS.md ]]
make verify-roadmap
python3 scripts/audit/commercial_readiness.py --wave 1 --format json --write
```

### 5.2 In-Flight Monitoring

- `PROGRESS.md` 의 "현재 진행률" 라인
- `.claude/ralph-loop.local.md` 의 `iteration` 값
- 블로커 발동 시 자동 정지 → HANDOFF.md 요약이 세션에 표시

### 5.3 Post-Completion Verification

`ONEERP_COMPLETE` 출력 후 사용자 확인:

```bash
python3 scripts/audit/commercial_readiness.py --wave 1 --format table
make roadmap-render && cat docs/product/roadmap/status.md
make verify-roadmap
./scripts/ci/run.sh
PROFILE=plane TIMEOUT=240 ./scripts/dev/stack-smoke.sh
./scripts/docs/audit-all.sh
```

모두 exit 0 이면 **M7 달성**.

---

## § 6. 범위 밖 (Out of Scope)

본 설계가 **다루지 않는** 것 — 오해 방지 목적으로 명시:

- **Wave 2~4 (M8~M10)**: 47 모듈 전체 상용화가 아니라 Wave 1 12 모듈 commercial-ready 까지만.
- **실제 파일럿 고객 확보 · 계약 · 운영 지원**: Q1 A 선택에 따라 제외. RELEASE-CRITERIA.md §Pilot Gate 의 "파일럿 고객 역할별 **시연 시나리오 준비**" 는 **포함** 되지만(G5-* 문서 게이트로 흡수), 실제 파일럿 고객을 받아 운영하는 활동은 루프 범위 밖.
- **외부 GTM 활동 (마케팅/영업)**: `services/marketing/gtm/` 모듈의 상용화도 Wave 1 미포함 (ADR-0012 참조).
- **프로덕션 배포 실측**: Phase 5 K8s manifest 는 dev/staging 에서만 자율 튜닝, 프로덕션 적용은 사용자 결정.
- **Backup/rollback 실측 리허설**: G4-3 / G4-4 판정은 정적 증거(문서 + dry-run 로그) 기반. 실제 데이터 복구 리허설은 분기 1회 사용자 주도.
- **AI/ML capability**: v2 요구사항 ADV-01 범위. M7 이후.

---

## § 7. 설계 외부 의존성 및 미해결 사항

본 설계가 전제하는 **외부 조건** (루프 내부에서 해결 불가):

1. **Docker 환경 상시 기동 가능**: compose up/down 을 루프가 반복 호출. Docker Desktop 이 꺼져 있으면 블로커 #11 발동.
2. **NATS JetStream 스트림 초기화 스크립트 안정**: `scripts/dev/init-nats-streams.sh` 가 멱등. 보장 안 되면 부트스트랩 #1~#5 flake.
3. **Core submodule 상태**: 현재 core/ 서브모듈의 미커밋 변경(사용자 작업 유지)은 cleanup 단계 1 에서 확인하며, 루프 가동 중에는 core/ 내부 미커밋 변경을 건드리지 않는다. 필요 시 사용자가 별도 세션에서 처리.
4. **context7 MCP 가용성**: 외부 라이브러리 최신 문서 조회용. 미가용 시 루프가 자체 지식으로 진행(질 저하 리스크).

### 미해결 사항 (시작 전 결정 필요 없으나 경과 중 관측 대상)

- `G1-4 unit coverage ≥90%` 를 자동으로 달성하는 테스트 역산 서브루틴의 품질 — flaky test 양산 가능성.
- `G3-3 multitenancy` 의 3단 격리 강제 메커니즘 — 기존 코드 리팩토링 범위가 어느 정도인지는 루프 실행 전 예측 불가.
- `G4-2 runbook` 템플릿 — 12 모듈 runbook 이 동일 템플릿으로 양산 가능한지 실측 후 판단.

---

## § 8. 승인 후 이어지는 작업

1. 본 문서 git commit
2. 사용자 최종 리뷰 (본 문서 그 자체)
3. `writing-plans` 스킬 호출 → 구현 계획 `docs/superpowers/plans/2026-04-16-ralph-loop-to-gtm.md` 작성
4. Pre-Loop Cleanup 6 단계 실행
5. `RALPH-LOOP-PROMPT.md` + `PROGRESS.md` 작성
6. `/ralph-loop:ralph-loop ...` 기동
7. 루프 완주 (ONEERP_COMPLETE) 또는 HANDOFF.md 에스컬레이션

---

## § 9. 참고 문서

- **Ralph-Loop skill**: `.claude/skills/ralph-loop/SKILL.md`
- **Plugin command**: `/Users/phil/.claude/plugins/cache/claude-plugins-official/ralph-loop/1.0.0/commands/ralph-loop.md`
- **Roadmap**: `.planning/ROADMAP.md`, `docs/product/roadmap/README.md`
- **Requirements**: `.planning/REQUIREMENTS.md`
- **23 품질 기준 정의**: `docs/governance/adr/0001-commercial-grade-definition.md`
- **Wave 매핑**: `docs/governance/adr/0012-commercialization-wave-mapping.md`
- **Phase 1~7 실행 계획**: `.planning/phases/0N-*/0N-01-PLAN.md`
- **Audit script**: `scripts/audit/commercial_readiness.py`
- **Roadmap gates**: `make verify-roadmap` → `scripts/roadmap/*.py`
- **Translation (어휘)**: `docs/product/roadmap/translation.md`
- **자가수정 규약**: `/Users/phil/.claude/CLAUDE.md` §"하네스 자율 엔지니어링"

---

*Last updated: 2026-04-16 by brainstorming session (/superpowers:brainstorming).*
