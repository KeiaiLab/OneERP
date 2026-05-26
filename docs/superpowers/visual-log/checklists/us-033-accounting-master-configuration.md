# US-033 — 회계 담당자는 계정과목, 회계기간, 원가센터, profit center를 관리한다

- Visual 키: `us-033-accounting-master-configuration`
- 저장 디렉토리: `docs/superpowers/visual-log/YYYY-MM-DD/us-033-accounting-master-configuration/`
- 대응 Playwright 키: `story_us_033_accounting_master_configuration`

## 캡처 목적

- 회계 문서가 올바른 기준값을 참조한다

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

- [ ] 마스터 등록, 기간 개설, 코스트 구조 정비
- [ ] 회계 문서가 올바른 기준값을 참조한다
- [ ] 긴 텍스트 overflow와 상태 배지가 템플릿 규약을 지킨다.
- [ ] primary action 위치가 스토리 타입 규약과 일치한다.
