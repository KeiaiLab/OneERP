# API 표준(초안)

## 원칙

- 외부 API와 내부 API를 경계로 분리한다.
- 인증/권한/감사로그는 “공통 커널”로 강제한다.
- API 변경은 ADR + 버저닝 정책에 따라 관리한다.

## Phase 0 현황

- **API 스타일**: REST (FastAPI) — 각 서비스 `app/routes/` 디렉토리에 라우트 정의
- **표준 에러 포맷**: `ErrorResponse(error, detail, request_id)` (`packages/core/oneerp_core/errors.py`)
- **추적 ID**: `X-Request-Id` 헤더 (`packages/core/oneerp_core/middleware.py`)
- **헬스체크**: `GET /health` → `{“status”: “ok”}` (모든 서비스 공통)

## 확인 필요(Phase 1)

- 이벤트/비동기 처리: 큐/워크플로우 엔진 선택(클러스터 인벤토리 기반)
- Observability 스택 연계 (구조화된 JSON 로깅 + 중앙 집계)
- GraphQL 도입 여부 (Phase 2에서 검토)

## 산출물(DoD)

- [x] 표준 에러 포맷/추적 ID 구현 완료
- [ ] API 계약(스키마/에러/권한 스코프)이 문서화됨
- [ ] E2E 시나리오가 API 계약을 기준으로 검증됨

