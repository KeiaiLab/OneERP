# 대규모 리팩토링 경계 가드레일

## 원칙

1. **shared kernel 은 얇게 유지한다.**
   - 허용: auth/tenant/errors/db/middleware/event schemas 같은 횡단 관심사
   - 금지: 도메인 규칙, 서비스별 상수, route 전용 persistence, plane 마운트 결정

2. **route→repository 직접 결합 금지.**
   - route 는 service/application layer 또는 주입된 port 만 호출한다.
   - `Repository(...)` 직접 인스턴스화와 `oneerp_core.repository` 직접 import 는 모두 차단 대상이다.

3. **plane 은 조립 전용이다.**
   - plane 은 mount / wire / bootstrap 만 담당한다.
   - 도메인 규칙, persistence, policy 를 plane 에 두지 않는다.
   - 실행형 truth 는 `planes/*/main.py` 와 worker `_EVENT_DOMAINS` 이다.

4. **service 는 도메인 규칙의 소유자다.**
   - route 와 plane 에 규칙을 밀어넣지 않는다.
   - shared kernel 으로 도메인 개념을 끌어올리지 않는다.

5. **FE 는 registry/contract 중심으로 다룬다.**
   - `EntityConfig.service` 와 `EntityConfig.entity` 가 canonical contract 이다.
   - OpenAPI drift, registry service-key drift, direct `apiFetch` bypass 를 각각 별도 경고로 본다.
   - generic CRUD 밖 direct `apiFetch` 는 예외 목록이 있어야 한다.

6. **deploy/docs 숫자와 경로는 실측 기준을 따른다.**
   - `deploy/catalog/services.yaml` 은 YAML key 실측을 따른다. 현재 기준선은 43개다.
   - `deploy/catalog/planes.yaml` 에 `includes:` 가 없으므로, plane 매핑은 문서가 아니라 실행 코드와 함께 본다.
   - `apps/web`, `services/gateway` 같은 구식 경로는 canonical reference 로 쓰지 않는다.

7. **wave 종료는 3조건 모두 충족해야 한다.**
   - deployable
   - rollbackable
   - test-green

## 금지 drift 목록

- shared kernel 에 도메인 규칙 추가
- route 가 repository 를 직접 import/instantiate
- plane 에 도메인 policy 추가
- FE registry 와 generated type 간 계약 불일치 방치
- direct `apiFetch` 우회 화면을 무기한 확장
- 문서 숫자를 실측보다 우선하는 서술
- catalog/CI/docs 의 구식 경로를 canonical 로 유지

## 허용 예외

- direct `apiFetch` 는 명시된 액션형 화면에서만 허용한다.
- legacy 문서와 경로는 삭제 대신 stale 표기로 잠시 보존할 수 있다.
- shared kernel 의 bootstrap/helper 는 가능하나 도메인 정책은 불가하다.

## 적용 기준

- 변경 전: 실측 근거를 먼저 확인한다.
- 변경 중: 경계 위반을 새로 만들지 않는다.
- 변경 후: wave 종료 3조건을 확인한다.
