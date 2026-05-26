# US-001 — 관리자는 테넌트와 회사를 개설하고 기본 운영 컨텍스트를 만든다

- Visual 키: `us-001-tenant-company-setup`
- 저장 디렉토리: `docs/superpowers/visual-log/YYYY-MM-DD/us-001-tenant-company-setup/`
- 대응 Playwright 키: `story_us_001_tenant_company_setup`

## 캡처 목적

- 활성 회사 컨텍스트가 저장되고 관리자 홈으로 진입한다

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

- [ ] 테넌트 생성, 회사 등록, 기본 통화/회계연도 연결
- [ ] 활성 회사 컨텍스트가 저장되고 관리자 홈으로 진입한다
- [ ] 긴 텍스트 overflow와 상태 배지가 템플릿 규약을 지킨다.
- [ ] primary action 위치가 스토리 타입 규약과 일치한다.
