# Compliance 클러스터 (compliance + clm 물리 병합)

**RUNBOOK S1~S14 파일럿 1호** — 2026-04-12 실측 성공.

## 병합 내용
- `services/compliance/compliance` (7 entity + risk_matrix route) → `app/compliance_mod/`
- `services/compliance/clm` (3 entity + event_registry) → `app/clm/`
- 단일 FastAPI 앱(`app.main:app`) 이 두 도메인 전 라우터·엔티티 호스팅

## 실측 결과
```
pytest tests/ -m "not integration and not e2e" → 34/34 passed
uv sync --package oneerp-compliance-merged → OK
```

## 라우트 prefix (BC 보존)
- `/api/v1/compliance-reports/*` (compliance)
- `/api/v1/risk-matrix/*` (compliance)
- `/api/v1/contract-templates/*` (clm)
- `/api/v1/contracts/*` (clm)
- `/api/v1/contract-renewals/*` (clm)

## 후속
- `deploy/catalog/services.yaml` 에서 compliance + clm 제거, compliance-merged 등록
- `docker-compose` 재생성
- Helm 차트 재정비
- 다른 12 클러스터 동일 절차 반복 (RUNBOOK S1~S14)
