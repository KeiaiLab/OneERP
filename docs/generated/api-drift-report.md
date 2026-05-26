# API Drift Report

- 코드 endpoint 수: 4
- docs endpoint 수: 1

> **수동 검토 필요**: 마크다운 파싱이 heuristic 이므로 false positive 가 있을 수 있습니다.

## [doc-orphan] docs 에만 존재 (2건)

- `GET /api/v1/sales-orders?page=2&page_size=10`
- `POST /api/v1/auth/login`

## [doc-missing] 코드에만 존재 (3건)

- `GET /health/live`
- `GET /health/ready`
- `GET /health/startup`

## [doc-skew] 필드 차이 (0건)

