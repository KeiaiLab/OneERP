# OneERP POS 서비스 (POS Service)

> POS(판매시점관리) 서비스 — Selling 서비스로 통합됨 / Point of Sale service — integrated into the Selling service

## 도메인 개요 (Domain Overview)

POS 관련 엔티티 (POS Entities) — pos_transaction, pos_closing_entry, pos_receipt 등 — 은 `services/selling/` 에서 구현되어 있다. 이 서비스는 독립 배포 대상이 아니며, uv workspace 호환성을 위해 유지된다.

## 기술 스택 (Tech Stack)

| 항목 (Item) | 기술 (Technology) |
|-------------|-------------------|
| 프레임워크 (Framework) | FastAPI + Pydantic v2 |
| 데이터베이스 (Database) | FerretDB (MongoDB Protocol) |
| 포트 (Port) | 8015 |

## POS 관련 기능 위치 (POS Feature Locations)

POS 기능은 Selling 서비스에서 관리한다 (POS features are managed in the Selling service):

| 기능 (Feature) | 위치 (Location) | 설명 (Description) |
|---------------|-----------------|-------------------|
| POS 거래 (POS Transaction) | services/selling/app/routes/pos_transactions.py | POS 거래 처리 (POS Transaction Processing) |
| POS 영수증 (POS Receipt) | services/selling/app/routes/pos_receipts.py | POS 영수증 관리 (POS Receipt Management) |
| POS 마감 (POS Closing) | services/selling/app/entities.py (POSClosingEntry) | POS 일마감 (POS Daily Closing) |
| POS 프로필 (POS Profile) | services/selling/app/entities.py (POSProfile) | POS 설정 (POS Configuration) |
| POS 결제수단 (POS Payment Method) | services/selling/app/entities.py (POSPaymentMethod) | POS 결제 수단 (POS Payment Methods) |

## 실행 방법 (How to Run)

```bash
uv run --package oneerp-pos --directory services/pos uvicorn app.main:app --port 8015
```

## 테스트 (Testing)

```bash
uv run pytest services/pos/ -m "not integration and not e2e" -v
```
