# 책임 매트릭스

이 문서는 OneERP의 구조 책임 기준선이다. 각 계층은 자신의 책임만 소유하고, 아래의 금지 책임과 허용 의존 방향을 따른다.

## 계층별 책임

| 계층 | 소유 책임 | 금지 책임 | 허용 의존 방향 |
|---|---|---|---|
| `core` | 공통 정책, 공용 계약, 순수 규칙, 재사용 가능한 도메인 원형 | HTTP/CLI/배포 조립, plane 전용 코드, 화면 상태 | 외부 의존 없음 |
| `services` | 도메인 유스케이스, 상태 변경, 저장소 포트, 서비스 단위 오케스트레이션 | plane 조립, UI 표현, 배포 자동화 | `core` |
| `planes` | 런타임 조립, HTTP/WebSocket/worker/scheduler/edge 어댑터, 프로세스 진입점 | 도메인 규칙의 직접 소유, 화면 로직, 배포 스크립트 | `services` → `core` |
| `web` | 화면 라우트, UI 상태, 사용자 상호작용, 프레젠테이션 로직 | 도메인 유스케이스의 직접 구현, plane 부트스트랩, 배포 스크립트 | `services` 계약 → `core` 공용 타입 |
| `deploy/scripts` | 빌드·배포·검증 자동화, 카탈로그/매니페스트 점검, 운영 스크립트 | 런타임 코드, 도메인 규칙, UI 로직 | `web`/`planes`/`services`/`core`를 참조하는 도구 코드만 허용 |

## 허용 의존 방향

- `core`는 다른 계층을 의존하지 않는다.
- `services`는 `core`만 의존한다.
- `planes`는 `services`와 `core`만 의존한다.
- `web`은 `services`의 공개 계약과 `core`의 공용 타입만 의존한다.
- `deploy/scripts`는 모든 계층을 검사하거나 실행할 수 있지만, 앱 런타임에서 import 되지 않는다.

## 금지 의존 방향

- `core -> services|planes|web|deploy/scripts`
- `services -> planes|web|deploy/scripts`
- `planes -> web|deploy/scripts`
- `web -> planes|deploy/scripts`
- `deploy/scripts -> runtime import`

## 참고

- ADR-0014의 6-plane 런타임 모델은 이 책임 기준선 위에서 조립된다.

## 착수 조건

다음 배치(planes 정리)는 아래 3개가 충족된 뒤에만 시작한다.

- scope SoT 공백 해소
- 구조 검사 baseline 확보
- release gate 성공
