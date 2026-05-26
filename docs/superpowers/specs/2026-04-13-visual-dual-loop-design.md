# 시각 이중 루프 개발 워크플로 설계

- 작성일: 2026-04-13
- 상태: 설계 승인 대기
- 대상 범위: OneERP `web/` 프런트엔드 작업 전반
- 파일럿: `app/login` (웜업) → `app/(modules)/[entity]` (본게임)

## 1. 배경과 목표

"실제 화면을 보면서 개발"하되, **사용자와 Claude가 각자 다른 시각 채널로 화면을 보고 역할을 분리**하는 이중 루프를 정착시킨다.

- **사용자**: 톤·흐름·의도·감성 — 기계가 볼 수 없는 품질을 판단한다.
- **Claude**: DOM·콘솔·네트워크·a11y·반응형 — 사람의 눈이 놓치는 기계적 회귀를 검증한다.

목표는 두 루프가 **서로를 방해하지 않으면서 증거를 남기도록** 규약을 고정하는 것이다. 본 설계의 산출물은 코드가 아니라 **규약과 파일럿 실행 계획**이다.

## 2. 아키텍처

```
[사용자 Chrome]           [dev 서버]              [Claude Chromium]
  localhost:3000   ←──   next dev --turbopack   ──→   localhost:3000
  (UX/톤 판단)            (백그라운드 Bash)          (chrome-devtools-mcp
                                                      DOM/콘솔/네트워크/
                                                      스크린샷/a11y)
                              │
                              ▼
                        코드 변경 (Claude Edit)
                              │
                              ├─ HMR → 양쪽 동시 갱신
                              │
                              └─ 예외 시: claude-in-chrome 전환
                                 (사용자 탭 직접 관찰)
```

### 구성 요소

| 요소 | 실체 | 기동 주체 | 수명 |
|------|------|-----------|------|
| dev 서버 | `pnpm --filter @oneerp/web dev` | Claude (백그라운드 Bash 1회) | 세션 내내 유지 |
| 사용자 브라우저 | 사용자 본인 Chrome | 사용자 | 사용자 관리 |
| Claude 검증 브라우저 | `chrome-devtools-mcp` 독립 Chromium | Claude | 필요 시 생성 |
| 공유 모드 관찰 | `claude-in-chrome` (사용자 탭 공유) | Claude | 예외 트리거 시만 |
| 증거 저장소 | `docs/superpowers/visual-log/YYYY-MM-DD/<topic>/` | Claude | 90일 후 아카이브 |

### 하이브리드 모드 스위치

기본은 **독립 모드**(`chrome-devtools-mcp`). 다음 3가지 트리거 중 하나일 때만 **공유 모드**(`claude-in-chrome`)로 전환:

1. 사용자가 "같이 봐줘"(또는 동의어) 명시 요청
2. 상호작용 버그 (클릭 순서·포커스·모달)
3. Claude 검증은 통과인데 사용자 화면에선 다르게 보일 때 (동기화 이슈 진단)

예외 루프 종료 후에는 독립 모드로 복귀한다.

## 3. 이터레이션 프로토콜 (1 사이클)

사용자가 지시한 순간부터 다음 지시까지:

1. **Baseline 캡처** — `take_screenshot` + `list_console_messages`
2. **코드 Edit** — 단일 목적, 최소 범위
3. **HMR 대기 + 사후 캡처** — `wait_for` → 스크린샷, 콘솔, 네트워크
4. **3단 자가검증**
   - ① 의도한 DOM 변화가 실제로 일어났나? (`take_snapshot` → 요소/텍스트 확인)
   - ② 회귀 신호 없나? (콘솔 에러 0, 4xx/5xx 0, 명백한 레이아웃 시프트 없음)
   - ③ a11y 기본선 유지? (주요 인터랙티브 요소 샘플링: role/label, focus 가능 여부)
5. **사용자 보고** — 한 단락 이내, 증거 경로 인용
   > "변경 완료. DOM/콘솔/a11y 자가검증 통과. 스크린샷: `<경로>`. 육안 확인 부탁."
6. **사용자 판단** — OK / 수정 / "같이 봐줘" 트리거
7. **사이클 마감** — `visual-log`에 before/after + 1줄 메모 append

### 역할 비월권 원칙

- Claude는 "예쁘다/안 예쁘다" 심미 판단을 **출력하지 않는다**.
- 사용자에게 콘솔 에러를 수동으로 점검하라고 **요청하지 않는다**.
- 두 채널의 증거가 **충돌**할 경우, 사용자 판단이 최종 — Claude는 가설을 바꾼다.

## 4. 파일럿 실행 계획

### 웜업: `app/login` (10~15분 목표)

목적: 루프 자체의 작동 검증. 화면 품질은 부차적.

- **0단계**: dev 서버 기동, Claude `new_page(localhost:3000/login)`, 사용자 본인 Chrome 동일 URL 오픈
- **1단계**: 의도적 사소한 변경 1개(예: 타이틀 문구, 여백) — 섹션 3의 1~5단계 전 과정 체험
- **2단계**: "같이 봐줘" 발화 1회 연습 — 공유 모드 왕복 후 독립 모드 복귀

**웜업 DoD**: before/after 스크린샷 쌍, 콘솔 에러 0건 로그, 공유 모드 왕복 1회 — `visual-log/2026-04-13/login/`에 파일로 존재.

### 본게임: `app/(modules)/[entity]` (다수 세션)

얕게 → 깊게 순서:

1. **리스트** (`/[entity]`): 로딩 / 빈 / 에러 / 정상 4상태
2. **상세** (`/[entity]/[id]`): 진입 / 수정 / 검증 에러 / 권한 없음 4시나리오
3. **신규** (`/[entity]/new`): 폼 검증, 키보드 네비, submit 실패 복구
4. **횡단 품질**: 반응형(sm/md/lg), a11y(keyboard-only), 테마(해당 시)

각 단계는 선도 엔티티 1개(예: `customers`)로 패턴 확정 후 전파 여부 결정.

**본게임 DoD (단계별)**:
- 각 상태/시나리오마다 스크린샷 + 콘솔 클린 + a11y 기본선 통과 기록이 `visual-log`에 존재
- 엔티티당 핵심 경로 1개에 대해 Playwright visual regression 스냅샷 추가

## 5. 산출물

| 경로 | 내용 | 수명 |
|------|------|------|
| `docs/superpowers/specs/2026-04-13-visual-dual-loop-design.md` | 본 문서 | 영구 |
| `.claude/skills/visual-dual-loop.md` | 매 세션 Claude가 따를 루프 규약 (프로토콜 기계 판독 형태) | 영구 |
| `docs/superpowers/visual-log/YYYY-MM-DD/<topic>/` | 사이클별 before/after + 메모 | 90일 후 아카이브 |
| `web/tests/e2e/visual/<entity>.spec.ts` | Playwright visual regression (본게임 산출) | 영구 |
| `AGENTS.md` 한 줄 추가 | "FE 작업 시 visual-dual-loop 스킬 준수" | 영구 |

## 6. 성공 기준

**워크플로 수준**
- 신규 Claude 세션이 스킬 파일만 읽고 루프를 동일 재현 가능
- Claude 단독으로 "자가검증 → 보고" 왕복 1회 완주 가능
- 공유/독립 모드 전환 트리거가 모호함 없이 1문장으로 식별됨

**파일럿 수준**
- 웜업: login의 before/after + 공유 모드 왕복 로그 존재
- 본게임: 선도 엔티티 `[entity]` 4상태 × visual-log + Playwright 스냅샷 공존

## 7. 열린 이슈

실행 단계에서 결정:

1. `visual-log` 저장 포맷 — PNG 단독 vs JSON 메타 동반 (웜업 종료 시점 결정)
2. Playwright visual regression 임계값 — 첫 스냅샷 3개 이후 경험적 설정
3. dev 서버 생존 관리 — 세션 종료 시 자동 kill vs 유지 (기본 제안: **유지**)

## 8. 범위 밖 (YAGNI)

본 설계에서 **명시적으로 제외**한다. 필요 시 별도 스펙으로 분리.

- Storybook 도입
- Lighthouse CI 자동화
- 디자인 토큰 / 피그마 동기화

## 9. 다음 단계

본 설계가 승인되면 `writing-plans` 스킬로 구현 플랜을 작성한다. 첫 구현 단위는:

1. `.claude/skills/visual-dual-loop.md` 스킬 파일 작성
2. `AGENTS.md` 한 줄 추가
3. `docs/superpowers/visual-log/` 디렉토리 초기화 + README
4. 웜업 실행 — login 대상 1 사이클

본게임은 별도 플랜으로 분리한다.
