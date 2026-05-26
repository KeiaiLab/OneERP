---
module: maintenance
baseline_date: 2026-04-22
---

# maintenance 부하 baseline

## 시나리오
80 rps × 10분. 설비 조회 + PM 예측 배치 + iot 이벤트 수신.

## 측정
| 지표 | 값 |
|---|---:|
| 설비 조회 p95 | 95ms |
| PM 예측 모델 추론 p95 | 210ms |
| iot 이벤트 처리량 | 1500/s sustained |

## 임계
- 이벤트 처리량 < 1200/s: backpressure.
