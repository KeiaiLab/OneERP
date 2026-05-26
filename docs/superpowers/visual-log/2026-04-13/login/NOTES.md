# login — 2026-04-13

## 사이클

- 1: baseline 캡처 (코드 변경 전)
- 2: `web/app/login/page.tsx` h1 여백 `mb-6` → `mb-8`. OneERP 타이틀과 폼 사이 간격 증가.

### After (after-1)
- DOM 검증: h1 "OneERP" level=1 유지, Fast Refresh 127ms 완료 (rebuild → done)
- 콘솔: error 3 / warn 3 — baseline 동일, 증가 0 (회귀 없음)
- 네트워크: 500 × 2 (baseline 동일, 새 4xx/5xx 없음)
- a11y: 사용자명·비밀번호 textbox required + label 연결 유지, 로그인 button focusable 유지

## 콘솔/네트워크 샘플

### Baseline (before-1)

**DOM 스냅샷 요약 (a11y 트리):**
- heading "OneERP" level=1
- textbox "사용자명" required (focus 가능, live "ㅁ" 값 — 이전 입력 잔존)
- textbox "비밀번호" required (focus 가능)
- button "로그인"
- alert atomic live="assertive" (폼 검증 용)
- Next.js Dev Tools 버튼 (개발 전용)

**콘솔 에러/경고 지표 (baseline 고정값):**
- error: 3건 (404 × 1, 500 × 2)
- warn: 3건 (CSS preload unused × 3)

**500 출처 (백엔드 게이트웨이 의존):**
- `GET /api/gateway/api/v1/me` → 500 (세션 체크)
- `POST /api/gateway/api/v1/auth/login` → 500 (이전 제출 흔적)

**판정 규칙:** 이 지표는 백엔드 미기동에 따른 기존 상태이다.
사이클 2 이후에는 **이 수치가 증가하지 않았는지**가 회귀 판정의 기준이다.

**a11y 기본선:**
- 인터랙티브 요소(textbox, button) 모두 role/label 존재
- 사용자명 textbox가 `focused` 상태로 초기 포커스 배치됨 — 양호
