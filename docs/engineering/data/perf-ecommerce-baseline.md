---
module: ecommerce
baseline_date: 2026-04-22
---

# ecommerce 부하 baseline

## 시나리오
400 rps × 10분. 카탈로그 조회 70% + 장바구니 업데이트 20% + 체크아웃 10%.

## 측정
| 지표 | 값 |
|---|---:|
| 카탈로그 p95 | 95ms |
| 장바구니 쓰기 p95 | 150ms |
| 체크아웃 p95 | 420ms (PG 포함) |
| RSS | 380MB |

## 임계
- 체크아웃 p95 > 483ms 회귀.
