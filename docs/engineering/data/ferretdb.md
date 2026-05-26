# 데이터 레이어: FerretDB(초안)

## Phase 0 현황

- DB 연결 관리: `packages/core/oneerp_core/db.py` (MongoClient 싱글턴 + 종료 훅)
- 기본 URI: `mongodb://localhost:27017`
- 기본 DB명: `oneerp`
- 통합 테스트: `packages/core/tests/integration/test_ferretdb_smoke.py` (ping 검증)

## 로컬 개발 표준

- `docker-compose.yml`로 FerretDB v2.7.0 + DocumentDB(Postgres) backend를 구동한다.
- 통합 테스트는 `./scripts/ci/run_integration.sh`로 실행한다.

## 운영 배치(확인 필요)

- 네임스페이스: (예: `data` 또는 전용)
- 스토리지: Rook-Ceph 기반 StorageClass 제약 반영(`docs/infra/inventory/k8s.md`)
- 백업/복구: `docs/infra/ops/backup-restore.md`

## FerretDB 제약(확인 필요)

- Mongo 호환 범위(쿼리/집계/트랜잭션/인덱스)
- 리포팅/집계 성능 목표

## 산출물(DoD)

- [ ] FerretDB 호환성 매트릭스: `docs/engineering/data/ferretdb-compat-matrix.md`
- [ ] 인덱스 표준: `docs/engineering/data/indexing-strategy.md`

