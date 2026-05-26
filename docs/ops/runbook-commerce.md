---
owner: Commerce Ops
host: commerce
modules: [ecommerce, subscriptions]
related_runbooks:
  - docs/ops/runbook-selling.md
  - docs/ops/runbook-incident-response.md
last_updated: 2026-04-22
---

# commerce (ecommerce + subscriptions) 운영 런북

commerce 플레인은 B2C/B2B e커머스와 구독 비즈니스를 번들 호스팅.

## ecommerce

스토어프론트·장바구니·체크아웃·주문. selling 의 고급 사례.

```bash
curl -s http://commerce:8000/v1/ecommerce/orders?state=pending
```

## subscriptions

반복 결제·갱신·이탈 관리. 정기과금 엔진.

```bash
curl -s http://commerce:8000/v1/subscriptions/renewals?due_today=true
```

## 자주 발생 이슈

| 증상 | 원인 | 조치 |
|---|---|---|
| 체크아웃 5xx | 외부 PG 의존성 | selling 런북의 A/B 전환 |
| 구독 갱신 실패 누적 | 결제 카드 만료 | dunning 파이프라인 확인 |
| 재고 동기 지연 | stock 이벤트 lag | stock 런북 참조 |

## 에스컬레이션

- Primary: `@commerce-ops`
- Cross: `@sales-ops`, `@finance-ops`
