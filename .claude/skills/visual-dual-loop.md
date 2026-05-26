---
name: visual-dual-loop
description: OneERP web/ FE 작업 시 사용자(UX)와 Claude(DOM/콘솔/a11y)가 각자 시각 채널로 화면을 관찰하며 역할 분리된 이중 루프로 개발한다. 모든 FE 변경 이터레이션마다 적용.
---

# 시각 이중 루프 (Visual Dual Loop)

## 언제 쓰는가
OneERP `web/` 내 FE 코드를 변경할 때마다 1 사이클 전체를 적용한다.

## 역할 분리
- **사용자**: 톤/흐름/의도/감성 — Claude는 심미 판단 출력 금지
- **Claude**: DOM/콘솔/네트워크/a11y/반응형 — 사용자에게 콘솔 수동 점검 요청 금지

## 브라우저 모드
- **기본 독립 모드**: `chrome-devtools-mcp` 로 Claude 전용 Chromium 사용
- **예외 공유 모드**: `claude-in-chrome` 으로 사용자 탭 직접 관찰. 아래 3 트리거 중 하나일 때만 전환:
  1. 사용자가 "같이 봐줘"(또는 동의어) 명시
  2. 상호작용 버그 (클릭 순서/포커스/모달)
  3. Claude 검증 통과이나 사용자 화면은 달라 보일 때
  사용 종료 후 독립 모드로 복귀.

## 세션 초기화 (최초 1회)
1. dev 서버 백그라운드 기동: `pnpm --filter @oneerp/web dev` (run_in_background)
2. Claude 검증 브라우저: `mcp__plugin_chrome-devtools-mcp_chrome-devtools__new_page` → `http://localhost:3000/<경로>`
3. 사용자에게 동일 URL을 본인 Chrome에서 열어달라고 고지

## 이터레이션 프로토콜 (1 사이클)
1. **Baseline 캡처**
   - `take_screenshot` → `docs/superpowers/visual-log/<YYYY-MM-DD>/<topic>/before-<n>.png`
   - `list_console_messages` 결과를 NOTES.md에 기록
2. **코드 Edit** (단일 목적, 최소 범위)
3. **HMR 대기 + 사후 캡처**
   - `wait_for` (적절한 signal)
   - `take_screenshot` → `after-<n>.png`
   - `list_console_messages`, `list_network_requests`
4. **3단 자가검증**
   - ① 의도한 DOM 변화 실제 발생? (`take_snapshot` → 요소/텍스트 확인)
   - ② 회귀 신호 없나? (콘솔 에러 0, 네트워크 4xx/5xx 0)
   - ③ a11y 기본선? (주요 인터랙티브 요소 role/label/focus 샘플링)
5. **사용자 보고** (한 단락):
   > "변경 완료. DOM/콘솔/a11y 자가검증 통과. 스크린샷: `<경로>`. 육안 확인 부탁."
6. **사용자 판단 수용** → OK / 수정 / "같이 봐줘" 트리거
7. **사이클 마감**: NOTES.md에 `- <n>: <1줄 메모>` append

## 충돌 규칙
Claude 검증과 사용자 판단이 충돌하면 **사용자 판단이 최종**. Claude는 가설을 바꾸고 재검증.

## 증거 저장소 규약
- 경로: `docs/superpowers/visual-log/<YYYY-MM-DD>/<topic>/`
- 필수 산출물: `before-<n>.png`, `after-<n>.png`, `NOTES.md`
- `<topic>`는 작업 대상(예: `login`, `customers-list`)

## 범위 밖
Storybook, Lighthouse CI, 피그마 동기화는 본 스킬 범위 아님.
