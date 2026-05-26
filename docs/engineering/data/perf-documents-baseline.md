---
module: documents
baseline_date: 2026-04-22
---

# documents 부하 baseline

## 시나리오
50 rps 업로드 × 10분. 평균 파일 크기 2MB.

## 측정
| 지표 | 값 |
|---|---:|
| 업로드 p95 | 520ms |
| 다운로드 p95 | 180ms |
| 메타데이터 검색 p95 | 95ms |
| S3 throttle 대응 재시도율 | 1.2% |

## 임계
- 업로드 p95 > 598ms 회귀.
