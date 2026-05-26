---
module: expenses
baseline_date: 2026-04-22
load_tool: k6
---

# expenses 부하 baseline

## 시나리오

- 80 rps × 10분, 경비 조회 + 신청 + 영수증 업로드.

## 측정

| 지표 | 값 |
|---|---:|
| 경비 조회 p95 | 120ms |
| 경비 신청 p95 | 180ms |
| 영수증 업로드 p95 (5MB) | 980ms (S3 포함) |
| fraud-detection 배치 | 42min (일일) |

## 임계

- 영수증 업로드 p95 > 1.2s: S3 엔드포인트 점검.
- fraud 배치 > 60min: 파이프라인 병렬화.
