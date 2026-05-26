---
module: subscriptions
baseline_date: 2026-04-22
---

# subscriptions 부하 baseline

## 시나리오
일 1회 갱신 배치 (10K 구독). dunning 파이프라인 병행.

## 측정
| 지표 | 값 |
|---|---:|
| 갱신 배치 | 28min |
| 갱신 성공률 | 96.8% |
| dunning 발송 rate | 500/min |

## 임계
- 갱신 배치 > 45min: 병렬화.
