# US-011 — 영업 담당자는 견적서를 작성해 고객에게 발송하고 응답을 추적한다

- Visual 키: `us-011-quotation-create-send-track`
- 저장 디렉토리: `docs/superpowers/visual-log/YYYY-MM-DD/us-011-quotation-create-send-track/`
- 대응 Playwright 키: `story_us_011_quotation_create_send_track`

## 캡처 목적

- 발송 이력과 수락/거절 상태가 기록된다

## 필수 캡처 체크리스트

- [ ] 정상 상태 캡처
- [ ] 빈 상태 캡처
- [ ] 오류 상태 캡처
- [ ] 로딩 상태 캡처
- [ ] 권한 없음 상태 캡처
- [ ] 모바일 상태 캡처

## 권장 파일명

- `before-normal.png`
- `before-empty.png`
- `before-error.png`
- `before-loading.png`
- `before-forbidden.png`
- `before-mobile.png`
- `after-normal.png`
- `after-empty.png`
- `after-error.png`
- `after-loading.png`
- `after-forbidden.png`
- `after-mobile.png`

## NOTES.md 체크리스트

- [ ] 실행 날짜와 브랜치/커밋을 기록한다.
- [ ] 사용한 URL, 계정, seed 또는 mock 조건을 기록한다.
- [ ] 콘솔/네트워크 이상 유무를 기록한다.
- [ ] before/after 차이와 판단 근거를 기록한다.
- [ ] 모바일 뷰포트 값을 기록한다.

## 사람 검증 포인트

- [ ] 견적 작성, PDF/메일 발송, 응답 상태 확인
- [ ] 발송 이력과 수락/거절 상태가 기록된다
- [ ] 긴 텍스트 overflow와 상태 배지가 템플릿 규약을 지킨다.
- [ ] primary action 위치가 스토리 타입 규약과 일치한다.
