---
chaos_id: chaos-manufacturing-2026-04-22
module: manufacturing
severity: P2-simulated
conducted_at: 2026-04-22T06:00:00Z
duration_minutes: 12
---

# chaos-manufacturing-2026-04-22 — MRP 재귀 폭주

## 가설
BOM 깊이 8 이상 재귀 계산 시 캐시 우회로 생산 API 전체 지연.

## 주입
인위적으로 BOM depth 10 인 가상 품목 추가, MRP 일괄 실행.

## 관측
- MRP 잡 13분 (baseline 3분).
- 생산 API p95 220→980ms 동안 지속.
- 캐시 TTL 연장으로 복구 후 정상.

## 결론
MRP 재귀 가드 필요 (depth 한도 설정).
