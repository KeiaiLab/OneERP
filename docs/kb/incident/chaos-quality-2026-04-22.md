---
chaos_id: chaos-quality-2026-04-22
module: quality
severity: P2-simulated
conducted_at: 2026-04-22T06:15:00Z
duration_minutes: 8
---

# chaos-quality-2026-04-22 — 검사 결과 수신 지연

## 가설
manufacturing 이벤트 버퍼 오버플로 시 quality 가 fallback 큐로 전환 후 정상 복귀.

## 주입
NATS consumer 일시 중단 5분.

## 관측
- 이벤트 지연 max 180초.
- fallback 큐 성공률 100%.
- 원상 복귀 후 큐 드레인 정상.

## 결론
fallback 메커니즘 정상. 큐 크기 모니터 강화 권장.
