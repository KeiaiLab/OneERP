# Gateway Identity 리팩토링 설계서

## 1. 배경

사용자 선택으로 1차 백엔드 리팩토링 웨이브는 `services/platform/gateway`의 `auth + users + me`를 대상으로 확정됐다.
이번 웨이브는 gateway 전체를 재작성하는 것이 아니라, 인증·사용자 관리·내 정보 조회를 하나의 **identity 서브도메인**으로 재정렬하는 작업이다.

현재 확인한 문제는 다음과 같다.

- `routes/auth.py`가 로그인, 리프레시, JWT 생성, 쿠키 기록, 역할→권한 조회를 한 파일에서 처리한다.
- `routes/users.py`가 사용자 CRUD뿐 아니라 초대 상태 계산, 인증 제공자 정규화, 상태 배지, 추천 액션, 요약 응답 조립까지 직접 수행한다.
- `routes/me.py`가 tenant/user repository를 직접 조회하며 enabled modules 계산까지 조합한다.
- `models/user.py`는 영속 모델과 요청 DTO(`UserCreate`, `UserUpdate`)를 같은 파일에 둔다.

즉 현재 문제는 “파일이 크다”보다 **라우트가 유스케이스·프레젠테이션·저장소 접근을 동시에 소유하는 구조**다.

## 2. 목표

이번 리팩토링의 목표는 다음 네 가지다.

1. 외부 API 계약(`/api/v1/auth/*`, `/api/v1/users/*`, `/api/v1/me`)은 유지한다.
2. gateway 내부에 identity 경계를 세워 인증, 사용자 워크벤치, 내 정보 조회 책임을 분리한다.
3. `route → service`, `models → dto`, `presentation 계산 분리` 패턴을 gateway에도 적용한다.
4. 구조 회귀를 막는 테스트를 추가한다.

## 3. 비목표

- JWT 방식 자체 변경
- 권한 모델 재설계
- OIDC 연동 정책 변경
- `oneerp_core`까지의 대규모 승격
- FE 응답 계약 변경

## 4. 접근안 비교

### 접근안 A. 얇은 헬퍼 추출

- `auth.py`, `users.py`, `me.py`에서 일부 함수만 별도 파일로 이동한다.
- 장점: 빠르다.
- 단점: identity 경계가 여전히 불명확하고, 라우트가 orchestration 책임을 계속 가진다.

### 접근안 B. gateway 내부 identity 서브도메인 도입

- gateway 내부에 인증, 토큰, 권한, 사용자 유스케이스, 사용자 프레젠터, 내 정보 조회를 분리한다.
- 장점: 외부 계약을 유지하면서 내부 책임을 가장 크게 정리할 수 있다.
- 단점: 파일 수가 늘고 초기 이동량이 있다.

### 접근안 C. 공통 로직을 `core/oneerp_core`로 승격

- 인증/사용자 공통 로직을 core 계층으로 끌어올린다.
- 장점: 장기적 공통화 가능.
- 단점: 첫 웨이브부터 blast radius가 과도하게 커진다.

### 선택

`접근안 B. gateway 내부 identity 서브도메인 도입`을 채택한다.
이는 첫 고강도 웨이브로 충분히 구조 개선 효과가 크면서도, `core`와 타 서비스까지 흔들지 않는 가장 안전한 선택이다.

## 5. 목표 구조

### 유지되는 파일

- `services/platform/gateway/oneerp_gateway_app/routes/auth.py`
- `services/platform/gateway/oneerp_gateway_app/routes/users.py`
- `services/platform/gateway/oneerp_gateway_app/routes/me.py`

위 라우트 파일은 삭제하지 않는다. 다만 라우트 엔드포인트 정의와 입출력 경계만 남기고, 나머지 책임은 아래 계층으로 이동한다.

### 신규/재구성 계층

- `dto.py`
  - `UserCreate`, `UserUpdate`, 인증 요청/응답 DTO를 모은다.
- `services/token_service.py`
  - access/refresh token 생성·검증, cookie write/delete 담당
- `services/permission_service.py`
  - 역할 목록에서 권한 목록을 계산
- `services/auth_service.py`
  - login / refresh / logout 유스케이스 조합
- `services/user_service.py`
  - 사용자 생성/수정/삭제/조회, 회사 검증, 초대·연동 상태 계산
- `services/user_presenter.py`
  - `status_badge`, `recommended_action`, `available_actions`, `access_summary`, `auth_summary`, `summary` 계산
- `services/me_service.py`
  - 현재 사용자 + tenant + enabled_modules 조합 조회

## 6. 책임 재배치 원칙

### auth

- 라우트는 `LoginRequest`를 받아 서비스 호출만 수행한다.
- tenant header fallback, 사용자 조회, 비밀번호 검증, active 검사, JWT 생성, refresh 검증은 서비스 계층으로 이동한다.
- cookie key(`token`, `refresh_token`)와 만료 정책은 유지한다.

### users

- 라우트는 CRUD 입구만 유지한다.
- 회사 존재 검증, auth provider 정규화, invitation status 계산, password hash 설정은 `user_service`로 이동한다.
- UI용 상태 배지/권장 액션/요약 응답은 `user_presenter`로 이동한다.

### me

- 라우트는 `me_service` 결과를 그대로 반환한다.
- tenant/user repository 조회, enabled modules 계산은 라우트에서 제거한다.

### models vs dto

- `models/user.py`에는 영속 모델 `User`와 enum만 남긴다.
- `UserCreate`, `UserUpdate`는 `dto.py`로 이동한다.

## 7. 데이터 흐름

### 로그인

`auth route` → `auth_service.login()` → `users repo 조회` → `password 검증` → `permission_service` → `token_service` → 응답/쿠키

### 리프레시

`auth route` → `auth_service.refresh()` → `token_service.decode_refresh()` → `users repo 재확인` → `token_service.issue_pair()`

### 사용자 목록/상세

`users route` → `user_service.list/get()` → `user_presenter.decorate_*()` → 응답

### 내 정보

`me route` → `me_service.get_me()` → `tenant/users repo 조회 + modules 계산` → 응답

## 8. 테스트 전략

### 경계 회귀 테스트

- `services/platform/gateway/tests/unit/test_route_boundary.py`
  - `auth.py`, `users.py`, `me.py`가 `Repository(`를 직접 사용하지 않는지 확인
- `services/platform/gateway/tests/unit/test_dto_boundary.py`
  - `models/user.py`에 `UserCreate`, `UserUpdate`가 남아 있지 않은지 확인

### 신규 단위 테스트

- `services/platform/gateway/tests/unit/test_token_service.py`
- `services/platform/gateway/tests/unit/test_auth_service.py`
- `services/platform/gateway/tests/unit/test_user_presenter.py`
- `services/platform/gateway/tests/unit/test_me_service.py`

### 기존 회귀 확인

- `services/platform/gateway/tests/unit/test_auth_routes.py`
- `services/platform/gateway/tests/unit/test_users.py`
- `services/platform/gateway/tests/unit/test_me.py`

## 9. 성공 기준

- `auth.py`, `users.py`, `me.py`에서 Repository 직접 접근이 제거된다.
- `models/user.py`에서 요청 DTO가 제거되고 `dto.py`로 이동한다.
- 기존 API 응답 계약과 쿠키/JWT 정책이 유지된다.
- gateway 단위 테스트와 신규 경계 테스트가 통과한다.

## 10. 실행 순서

1. DTO 분리 (`models/user.py` → `dto.py`)
2. token / permission 서비스 추출
3. auth 유스케이스를 `auth_service`로 이동
4. user CRUD/정규화 로직을 `user_service`로 이동
5. 사용자 워크벤치 가공을 `user_presenter`로 이동
6. `me_service` 도입
7. 경계 회귀 테스트와 기존 gateway 테스트로 검증
