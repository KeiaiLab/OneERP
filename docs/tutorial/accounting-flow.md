---
module: accounting
gate: G5-2
tier: "T1+T2"
audience: developer operator finance-admin
last_updated: 2026-04-22
spec_version: Commercial Grade v2
evidence_line_target: 400
---

# accounting 전체 플로우 튜토리얼

> 대상: 개발자 · 운영자 · 재무 관리자
> 최종 갱신: 2026-04-22 (Commercial Grade v2 · Spec III Wave B-2)
> 게이트: G5-2 튜토리얼 증거

본 튜토리얼은 accounting 서비스를 처음부터 끝까지 한 번 돌려보는 과정을
step-by-step 으로 따라간다. 각 단계는 로컬 환경을 전제로 하며, 스테이징
인프라가 없어도 단위 수준에서 검증할 수 있도록 대안 명령을 함께 제공한다.

전체 흐름:

```
① 환경 구성 → ② 회계기간 설정 → ③ 전표 생성 → ④ 예산 설정
→ ⑤ 전표 결재 → ⑥ 세금 신고 데이터 추출 → ⑦ 문제 해결
```

## Step 1 · 환경 구성

### 1.1 레포 clone 및 의존성 설치

```bash
git clone https://github.com/example/OneErp.git
cd OneErp
uv sync --all-extras
```

### 1.2 필수 환경변수

`~/.bashrc` 또는 세션 환경에 설정.

```bash
export ONEERP_JWT_SECRET="dev-secret-key-minimum-32-bytes-for-local-development-only-okay"
export ONEERP_DEBUG=true
export ONEERP_DB_URL="mongodb://localhost:27017/oneerp"
```

> 주의: `ONEERP_JWT_SECRET` 는 32 bytes 이상이어야 `CoreSettings` 검증을
> 통과한다. 프로덕션에서는 반드시 ExternalSecrets 로 주입한다.

### 1.3 FerretDB 기동

```bash
docker run -d --name ferretdb -p 27017:27017 \
  -e FERRETDB_HANDLER=pg \
  -e FERRETDB_POSTGRESQL_URL=postgres://user:pass@host:5432/ferret \
  ghcr.io/ferretdb/ferretdb:2.7.0
```

### 1.4 accounting 서비스 기동

```bash
uv run --package oneerp-accounting \
       --directory services/finance/accounting \
       uvicorn oneerp_accounting_app.main:app --port 8010
```

### 1.5 Health check

```bash
curl -s http://localhost:8010/health | jq .
# {"status":"ok","service":"accounting",...}
```

## Step 2 · 회계기간 설정

### 2.1 회계연도 생성

```bash
curl -s -X POST http://localhost:8010/api/v1/fiscal-years \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant-demo" \
  -H "Authorization: Bearer ${JWT}" \
  -d '{
    "code": "FY2026",
    "start_date": "2026-01-01",
    "end_date": "2026-12-31",
    "status": "open"
  }' | jq .
```

### 2.2 월별 회계기간 생성

12 개월을 루프로 생성한다.

```bash
for m in 01 02 03 04 05 06 07 08 09 10 11 12; do
  curl -s -X POST http://localhost:8010/api/v1/accounting-periods \
    -H "Content-Type: application/json" \
    -H "X-Tenant-ID: tenant-demo" \
    -H "Authorization: Bearer ${JWT}" \
    -d "{
      \"fiscal_year_code\": \"FY2026\",
      \"code\": \"FY2026-${m}\",
      \"start_date\": \"2026-${m}-01\",
      \"end_date\": \"2026-${m}-28\",
      \"status\": \"open\"
    }"
done
```

### 2.3 기간 상태 확인

```bash
curl -s http://localhost:8010/api/v1/accounting-periods?status=open \
  -H "X-Tenant-ID: tenant-demo" \
  -H "Authorization: Bearer ${JWT}" | jq '.[].code'
```

## Step 3 · 전표 엔트리 생성

### 3.1 매출 전표 초안 작성

```bash
JOURNAL_ID=$(curl -s -X POST http://localhost:8010/api/v1/journal-entries \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant-demo" \
  -H "Authorization: Bearer ${JWT}" \
  -d '{
    "period_id": "FY2026-04",
    "description": "4월 제품 매출",
    "lines": [
      {"account_code": "1100", "debit": 1100000, "credit": 0},
      {"account_code": "4000", "debit": 0, "credit": 1000000},
      {"account_code": "2500", "debit": 0, "credit": 100000}
    ]
  }' | jq -r '.id')
echo "created journal: ${JOURNAL_ID}"
```

> 차대변 합계 불일치 시 `422 Unprocessable Entity` 가 반환된다.

### 3.2 Python 코드로 동일 작업

```python
from __future__ import annotations

import httpx

async def create_journal(client: httpx.AsyncClient, jwt: str) -> str:
    response = await client.post(
        "/api/v1/journal-entries",
        headers={
            "Authorization": f"Bearer {jwt}",
            "X-Tenant-ID": "tenant-demo",
        },
        json={
            "period_id": "FY2026-04",
            "description": "4월 제품 매출",
            "lines": [
                {"account_code": "1100", "debit": 1_100_000, "credit": 0},
                {"account_code": "4000", "debit": 0, "credit": 1_000_000},
                {"account_code": "2500", "debit": 0, "credit": 100_000},
            ],
        },
    )
    response.raise_for_status()
    return response.json()["id"]
```

### 3.3 전표 목록 확인

```bash
curl -s "http://localhost:8010/api/v1/journal-entries?status=draft" \
  -H "X-Tenant-ID: tenant-demo" \
  -H "Authorization: Bearer ${JWT}" | jq .
```

## Step 4 · 예산 설정

### 4.1 원가 센터 생성

```bash
curl -s -X POST http://localhost:8010/api/v1/cost-centers \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant-demo" \
  -H "Authorization: Bearer ${JWT}" \
  -d '{"code":"CC-SALES","name":"영업본부","parent_code":null}' | jq .
```

### 4.2 연간 예산 수립

```bash
BUDGET_ID=$(curl -s -X POST http://localhost:8010/api/v1/budgets \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant-demo" \
  -H "Authorization: Bearer ${JWT}" \
  -d '{
    "fiscal_year_code": "FY2026",
    "cost_center_code": "CC-SALES",
    "amount_by_period": {
      "FY2026-01": 100000000,
      "FY2026-02": 100000000,
      "FY2026-03": 120000000,
      "FY2026-04": 120000000
    },
    "status": "draft",
    "enforce_limit": true
  }' | jq -r '.id')
echo "budget: ${BUDGET_ID}"
```

### 4.3 예산 확정

```bash
curl -s -X PATCH "http://localhost:8010/api/v1/budgets/${BUDGET_ID}/confirm" \
  -H "X-Tenant-ID: tenant-demo" \
  -H "Authorization: Bearer ${JWT}" | jq .
```

## Step 5 · 전표 결재 (submit → approve → post)

### 5.1 submit

```bash
curl -s -X PATCH "http://localhost:8010/api/v1/journal-entries/${JOURNAL_ID}/submit" \
  -H "X-Tenant-ID: tenant-demo" \
  -H "Authorization: Bearer ${JWT}" | jq .
```

### 5.2 approve (`accounting.approver` 역할 필요)

```bash
curl -s -X PATCH "http://localhost:8010/api/v1/journal-entries/${JOURNAL_ID}/approve" \
  -H "X-Tenant-ID: tenant-demo" \
  -H "Authorization: Bearer ${JWT_APPROVER}" | jq .
```

### 5.3 post

```bash
curl -s -X PATCH "http://localhost:8010/api/v1/journal-entries/${JOURNAL_ID}/post" \
  -H "X-Tenant-ID: tenant-demo" \
  -H "Authorization: Bearer ${JWT_APPROVER}" | jq .
```

`post` 시점에 다음 이벤트가 발행된다.

- `journal_entry.posted` — analytics/audit/budget 소비
- `general_ledger_entry.created` — 총계정원장 반영

### 5.4 역분개 (필요 시)

```bash
curl -s -X POST "http://localhost:8010/api/v1/journal-entries/${JOURNAL_ID}/reverse" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant-demo" \
  -H "Authorization: Bearer ${JWT_APPROVER}" \
  -d '{"reason":"금액 오류 정정"}' | jq .
```

## Step 6 · 세금 신고 데이터 추출

### 6.1 부가세 신고 초안

```bash
VAT_ID=$(curl -s -X POST http://localhost:8010/api/v1/vat-returns \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant-demo" \
  -H "Authorization: Bearer ${JWT_TAX}" \
  -d '{
    "period": "2026Q2",
    "return_type": "regular"
  }' | jq -r '.id')
```

### 6.2 국세청 계산 검증

```bash
curl -s -X PATCH "http://localhost:8010/api/v1/vat-returns/${VAT_ID}/prepare" \
  -H "X-Tenant-ID: tenant-demo" \
  -H "Authorization: Bearer ${JWT_TAX}" | jq .
```

### 6.3 제출

```bash
curl -s -X POST "http://localhost:8010/api/v1/vat-returns/${VAT_ID}/submit" \
  -H "X-Tenant-ID: tenant-demo" \
  -H "Authorization: Bearer ${JWT_TAX}" | jq .
# 202 Accepted — 비동기
```

### 6.4 상태 폴링

```bash
while true; do
  STATUS=$(curl -s "http://localhost:8010/api/v1/vat-returns/${VAT_ID}" \
    -H "X-Tenant-ID: tenant-demo" \
    -H "Authorization: Bearer ${JWT_TAX}" | jq -r '.status')
  echo "status: ${STATUS}"
  [[ "${STATUS}" == "accepted" || "${STATUS}" == "rejected" || "${STATUS}" == "failed" ]] && break
  sleep 30
done
```

### 6.5 전자세금계산서 발급

```bash
curl -s -X POST http://localhost:8010/api/v1/etax-invoices \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant-demo" \
  -H "Authorization: Bearer ${JWT_TAX}" \
  -d '{
    "invoice_type": "sales",
    "buyer_biz_no": "123-45-67890",
    "supply_amount": 1000000,
    "vat_amount": 100000,
    "item_name": "제품 A"
  }' | jq .
```

### 6.6 원천세 추출

```bash
curl -s "http://localhost:8010/api/v1/withholding-tax?period=2026-04" \
  -H "X-Tenant-ID: tenant-demo" \
  -H "Authorization: Bearer ${JWT_TAX}" | jq .
```

## Step 7 · 문제 해결

### 7.1 422 — 차대변 합계 불일치

- 원인: `lines[].debit` 합 ≠ `lines[].credit` 합.
- 조치: 합계 재확인. `debit + credit` 이 아닌 각각의 합이 같아야 한다.

### 7.2 409 — 기간이 closed

- 원인: 전표의 `period_id` 가 이미 마감된 기간.
- 조치: 당기로 이동하거나, `accounting.closer` 권한으로 reopen.

### 7.3 401 — JWT 만료

```bash
# 새 JWT 발급
JWT=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo"}' | jq -r '.access_token')
```

### 7.4 403 — scope 부족

- gateway 의 OPA 정책 또는 keycloak 역할 매트릭스에서 권한 부여 확인.

### 7.5 500 — 국세청 Open API 응답 없음

- `nts_api_client` 로그에서 HTTP 상태·에러 메시지 확인.
- `status=failed` 인 신고 건은 자동 재시도 큐 대상.
- 72 시간 초과 시 수동 전환.

### 7.6 단위 테스트로 검증

```bash
uv run pytest services/finance/accounting/tests/unit -v
```

### 7.7 보안 테스트 (AuthN 7 종)

```bash
uv run pytest services/finance/accounting/tests/security -v
```

로컬(스테이징 없음) 에서는 전부 skipped 로 통과하는 것이 정상.

## 부록 A · 권한별 JWT 생성 스니펫

```python
from __future__ import annotations

import jwt
import time

def make_jwt(subject: str, roles: list[str], secret: str) -> str:
    now = int(time.time())
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + 3600,
        "aud": "oneerp",
        "iss": "oneerp-dev",
        "scope": " ".join(roles),
    }
    return jwt.encode(payload, secret, algorithm="HS256")

# 사용 예
jwt_tax = make_jwt("user-tax", ["accounting.tax"], secret="...")
```

## 부록 B · 이벤트 체인 관찰

NATS 기반 이벤트 스트림을 `nats sub` 로 구독하여 실습한다.

```bash
nats sub 'accounting.>' --count 5
# journal_entry.posted → general_ledger_entry.created → audit.emit 순서 확인
```

## 부록 C · FerretDB 데이터 직접 조회

```bash
mongosh mongodb://localhost:27017/oneerp
db.journal_entries.find({tenant_id: "tenant-demo", status: "posted"}).limit(5)
db.audit_events.find({action: /accounting\./}).sort({ts: -1}).limit(10)
```

> 운영 환경에서는 직접 DB 조회를 금지한다. 감사 로그에 흔적이 남지 않기
> 때문이다. 본 실습에서만 로컬 용도로 사용한다.

## 부록 D · 자동화 스크립트 예시

전체 플로우를 한 번에 돌리는 예시 스크립트. `tests/integration/accounting`
에 유사한 검증 코드가 존재한다.

```python
from __future__ import annotations

import asyncio
import httpx


async def full_flow() -> None:
    async with httpx.AsyncClient(base_url="http://localhost:8010") as client:
        # 1. 기간 생성 생략 (시드 데이터 가정)
        # 2. 전표 draft
        resp = await client.post(
            "/api/v1/journal-entries",
            headers={"X-Tenant-ID": "tenant-demo"},
            json={
                "period_id": "FY2026-04",
                "description": "튜토리얼 검증",
                "lines": [
                    {"account_code": "1100", "debit": 100, "credit": 0},
                    {"account_code": "4000", "debit": 0, "credit": 100},
                ],
            },
        )
        resp.raise_for_status()
        jid = resp.json()["id"]

        # 3. 결재 체인
        for action in ("submit", "approve", "post"):
            r = await client.patch(
                f"/api/v1/journal-entries/{jid}/{action}",
                headers={"X-Tenant-ID": "tenant-demo"},
            )
            r.raise_for_status()
            print(f"{action} OK: {r.json()['status']}")


if __name__ == "__main__":
    asyncio.run(full_flow())
```

## 부록 E · 참조

- ADR-0019 Accounting 클러스터 경계 정의 (`docs/kb/adr/0019-accounting-bounds.md`)
- OpenAPI 스텁 (`services/finance/accounting/openapi.yaml`)
- 운영 매뉴얼 (`docs/manual/accounting.md`)
- 70 엔드포인트 상세: `services/finance/accounting/oneerp_accounting_app/routes/*.py`
- 23 도메인 서비스: `services/finance/accounting/oneerp_accounting_app/services/*.py`
- Spec III 플랜: `docs/superpowers/plans/2026-04-22-spec3-staging-quality.md` Wave B-2

## Change Log

| 일자 | 변경 | 근거 |
|------|------|------|
| 2026-04-22 | 최초 작성 (G5-2 L0) | Spec III Wave B-2 Task B2-9 박제 |
