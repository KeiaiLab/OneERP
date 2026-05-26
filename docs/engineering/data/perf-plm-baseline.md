---
module: plm
baseline_date: 2026-04-22
---

# plm 부하 baseline

## 시나리오
40 rps × 10분. BOM 편집 + ECN 제출 + 도면 다운로드.

## 측정
| 지표 | 값 |
|---|---:|
| BOM 쓰기 p95 | 220ms |
| ECN 제출 p95 | 310ms |
| 도면 다운로드 p95 | 680ms (documents 의존) |

## 임계
- BOM 쓰기 > 253ms: 트리 쓰기 최적화.
