---
module: gateway
retention_hot: 90 days
retention_cold: 3 years
last_reviewed: 2026-04-22
---

# gateway 감사 이벤트 보존 정책

## 요약

gateway 가 발행하는 감사 이벤트의 보존 기간·저장 계층·접근 통제.

## 보존 계층

### Hot (90 일)
- 저장소: FerretDB `audit_events` 컬렉션
- 인덱스: `(entity_type, entity_id, timestamp)`
- 쿼리 가능: `/api/v1/admin/audit-events`

### Cold (3 년)
- 저장소: S3 객체 스토리지 (`s3://oneerp-audit-archive/gateway/YYYY/MM/`)
- 형식: Parquet 압축
- 접근: 감사 복구 절차 (`docs/ops/runbook-gateway.md` §"복구 절차")

## 이벤트 스키마

```json
{
  "event_id": "uuid",
  "action": "gateway.create | gateway.update | gateway.delete | gateway.submit | gateway.approve | gateway.reject | gateway.cancel",
  "actor": "user-uuid",
  "tenant_id": "tenant-uuid",
  "resource": "tenant/{id} | approval_request/{id} | approval_action/{id}",
  "timestamp": "2026-04-22T00:00:00Z",
  "details": {},
  "source": "gateway"
}
```

## 감사 대상 route

| HTTP 메서드 | 경로 | 액션 |
|------------|------|------|
| POST | `/api/v1/admin/tenants` | `gateway.create` |
| PUT | `/api/v1/admin/tenants/{id}` | `gateway.update` |
| POST | `/api/v1/admin/tenants/{id}/suspend` | `gateway.update` |
| POST | `/api/v1/tenants` | `gateway.create` |
| PUT | `/api/v1/tenants/{id}` | `gateway.update` |
| DELETE | `/api/v1/tenants/{id}` | `gateway.delete` |
| POST | `/api/v1/approval-requests` | `gateway.create` |
| POST | `/api/v1/approval-requests/{id}/submit` | `gateway.submit` |
| POST | `/api/v1/approval-requests/{id}/cancel` | `gateway.cancel` |
| POST | `/api/v1/approval-actions` | `gateway.submit` |

## 규정 준수

- ISO 27001 A.12.4 (logging)
- SOC 2 CC6.1 (access monitoring)
- 개인정보보호법 제29조 (접근 기록)

## 검증 절차

```bash
# 최근 24 시간 이벤트 수
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://gateway.local/api/v1/admin/audit-events?since=24h" | jq '.events | length'

# 3 개월 전 이벤트 존재 (Cold 백업 접근)
aws s3 ls s3://oneerp-audit-archive/gateway/2026/01/
```

## 관련

- 런북: `docs/ops/runbook-gateway.md`
- ADR: `docs/governance/adr/gateway-commercial-v2.md`
- OWASP 체크리스트: `docs/security/OWASP-CHECKLIST.md`
