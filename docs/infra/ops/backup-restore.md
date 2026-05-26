# 백업/복구(초안)

## 범위

- FerretDB 데이터(backend Postgres 포함)
- 파일/오브젝트 스토리지 업로드
- 구성(시크릿 제외) 및 마이그레이션 정의

## 확인 필요(Phase 0)

- 백업 저장소/암호화/KMS
- RPO/RTO
- 복구 리허설 주기 및 책임자

## 모니터링 연계

- 백업 작업 성공/실패 메트릭 → Observability 스택으로 수집 (`docs/infra/ops/observability.md`)
- 백업 실패 시 알림 → SLO 기반 알림 채널과 동일 경로

## DoD

- [ ] 백업이 자동화됨
- [ ] 복구 리허설 1회 이상 통과(증빙 포함)
- [ ] 백업 상태 메트릭이 Observability 스택에 수집됨

