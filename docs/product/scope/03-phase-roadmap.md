---
title: OneERP 서비스 Phase Roadmap
date: 2026-04-22
status: active
owner: product-scope-wg
---

# Phase Roadmap

OneERP 서비스 배치 로드맵이다. `support` 서비스는 본 로드맵에서 사용하지 않는다
(카탈로그에서도 제거되어 있음).

## 서비스 단계

| phase | service | 비고 |
|-------|---------|------|
| P1 | accounting | PaymentEntry · JournalEntry · Invoice 회계 코어 |
| P1 | sales | SalesOrder · Quotation |
| P1 | scm | PurchaseOrder · StockEntry |
| P2 | hr | Employee · LeaveApplication |
| P2 | finance | 예산/재무 계획 |
| P2 | logistics | DeliveryNote · 출하 |
| P3 | marketing | Campaign |
| P3 | collab | Workspace |
| P3 | compliance | Policy |
| P3 | ehs | Incident |
| P4 | platform | Tenant |
| P4 | portal | PortalUser |
| P4 | deploy | Release |

## 금지 사항

- `support` 서비스는 본 로드맵에서 제공되지 않는다.
  고객 지원 워크플로는 `collab` 또는 외부 연동으로 해결한다.
