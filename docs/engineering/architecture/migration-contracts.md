# migration contract 규약

## 목적

- API, 이벤트, 배포 카탈로그 변경을 하나의 contract gate 묶음으로 다룬다.
- breaking/non-breaking 여부와 관계없이 변경은 반드시 검출 가능해야 한다.
- 데이터/이벤트 마이그레이션은 expand/migrate/contract 3단계로 고정한다.

## 3단계 원칙

### 1. expand

- 새 API 필드, 새 이벤트 필드, 새 deploy/catalog entry를 **기존 계약과 공존 가능**한 방식으로 먼저 추가한다.
- producer는 old/new를 함께 쓸 수 있어야 하고, consumer는 old/new를 함께 읽을 수 있어야 한다.
- 이 단계에서는 기존 필드/이벤트/카탈로그 키를 제거하지 않는다.

### 2. migrate

- 데이터 backfill, consumer 전환, 운영 설정 전환을 수행한다.
- 이벤트의 경우 producer/consumer dual-write 또는 dual-read를 허용한다.
- schema_version 증가가 필요한 breaking change는 이 단계에서 rollout 계획을 갖춘다.

### 3. contract

- old path, old field, old event, old catalog entry를 제거한다.
- 제거는 migrate 완료 증거가 있을 때만 수행한다.
- contract 단계에서도 검출 게이트는 유지한다. 제거는 검출 면제가 아니다.

## API / 이벤트 / deploy catalog gate 묶음

- OpenAPI 타입 생성/드리프트 검출: `scripts/ci/gen_openapi_types.sh`, `scripts/ci/check_openapi_drift.sh`
- OpenAPI schema contract 및 deploy validate 묶음: `scripts/ci/run_contract_tests.sh`
- deploy catalog SoT 검증: `uv run python -m scripts.deploy validate`

`run_contract_tests.sh`는 contract gate 묶음의 일부로서 OpenAPI 스키마 검증 후 `scripts.deploy validate`를 실행한다. 즉 배포 카탈로그 검증은 별도 운영 체크가 아니라 contract gate 체인에 포함된다.

## deploy/catalog validate와의 관계

- `deploy/catalog/`는 배포 계약의 선언형 SoT다.
- API나 이벤트가 서비스 경계/배포 단위를 바꾸면 catalog도 같이 검증해야 한다.
- 따라서 contract change 검토는 코드 diff만으로 끝내지 않고 `uv run python -m scripts.deploy validate`까지 포함해야 한다.

## breaking change 허용 조건

- breaking change 자체는 금지하지 않는다.
- 단, 다음은 필수다.
  1. 변경이 breaking임을 문서에 명시
  2. expand/migrate/contract 단계 분리
  3. gate에서 검출 가능해야 함
  4. deploy/catalog validate 포함 검증 증거 남김

즉, **breaking change 허용 ≠ 검출 면제**다. 검출되지 않는 breaking change가 가장 큰 실패다.

## 최소 운영 체크리스트

- OpenAPI drift 스크립트가 현재 서비스 경로와 `web/lib/types/generated`를 사용한다.
- contract 테스트가 현재 서비스 패키지 경로에서 스키마를 추출한다.
- deploy catalog validation이 contract gate 묶음에 포함된다.
- 이벤트 `schema_version` 및 migration 원칙이 문서로 고정된다.
