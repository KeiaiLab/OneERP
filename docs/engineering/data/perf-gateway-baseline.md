---
module: gateway
baseline_date: 2026-04-22
load_tool: k6
---

# gateway 부하 baseline

## 테스트 시나리오

- **target**: 1000 rps × 10분 sustained, ramp-up 2분.
- **traffic**: 70% GET / 20% POST / 10% other.
- **auth**: 99% valid JWT, 1% invalid (auth 실패 경로 점검).
- **tenant mix**: 10 테넌트 균등.

## 측정 결과

| 지표 | 값 |
|---|---:|
| p50 latency | 72ms |
| p95 latency | 180ms |
| p99 latency | 340ms |
| throughput | 985 rps (98.5% target) |
| error rate | 0.08% |
| RSS memory | 420MB |
| CPU user | 38% |

## 임계치 (회귀 탐지)

- p95 > 210ms (baseline +15%): 회귀 플래그.
- RSS > 500MB (+20%): 회귀.
- CPU > 48% (+25%): 회귀.
- error rate > 0.2%: 즉시 롤백 검토.

## 다음 측정

- 분기 1회, 또는 upstream 모듈 메이저 배포 직후.
- regression.py 로 자동 비교: `uv run python scripts/perf/regression.py --module gateway`.
