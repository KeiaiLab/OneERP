---
chaos_id: chaos-stock-2026-04-22
module: stock
severity: P1-simulated
conducted_at: 2026-04-22T04:45:00Z
duration_minutes: 22
type: chaos-engineering
---

# chaos-stock-2026-04-22 — 품절 연쇄 영향

## 가설

베스트셀러 SKU 동시 품절 시 emergency reserve bypass 로 selling 주문
수신 지속 (backorder queue 활용).

## 주입

SKU `BESTSELLER-101` 잔고를 0으로 인위 조정, 동시 selling 주문 50건 시뮬.

## 관측

- selling 주문 수락률: 100% (backorder queue 경유).
- emergency bypass 플래그 5분 내 자동 해제 (재고 복구 후).
- manufacturing ATP 경보 적절히 발동.

## 결론

- 주문 수신 중단 없음 ✓
- selling/stock/manufacturing 3자 협업 확인.

## 개선

- bypass 해제 조건이 재고 임계치만 기반 — 안전재고 회복 지속 시간도 고려 필요.
