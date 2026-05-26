# 튜토리얼: Asset Lifecycle (자산 생애주기) / Tutorial: Asset Lifecycle

## 개요 (Overview)

자산 등록 (Registration)에서 감가상각 (Depreciation), 부서 간 이동 (Transfer),
재평가 (Revaluation), 처분 (Disposal)까지의 전체 자산 생애주기를 단계별로 실습한다.
이 시나리오는 Assets 서비스의 `DepreciationService`와 `AssetLifecycleService`를 활용한다.

This tutorial covers the complete asset lifecycle — from registration through depreciation,
inter-department transfer, revaluation, and disposal.

## 사전 조건 (Prerequisites)

- Assets, Accounting 서비스가 로컬에서 기동되어 있어야 한다.
- 자산 마스터와 상각 규칙이 준비되어 있어야 한다.
- 자산 이동/처분 이력을 확인할 권한이 필요하다.

## 완료 조건 (Completion Criteria)

- 자산 등록, 감가상각, 이동, 처분 흐름이 완료된다.
- 자산 가치 변동과 회계 반영을 확인할 수 있다.
- 다음 프로젝트 관리 튜토리얼로 이동할 수 있다.

## 다음 단계 (Next Step)

- [프로젝트 관리 튜토리얼](./07-project-management.md)

## 사전 준비 (Prerequisites)

### 서비스 기동 (Start Services)

```bash
# Assets (포트 8010 / Port 8010)
uv run --package oneerp-assets --directory services/assets \
    uvicorn app.main:app --port 8010 --reload

# Accounting (포트 8005 / Port 8005)
uv run --package oneerp-accounting --directory services/accounting \
    uvicorn app.main:app --port 8005 --reload
```

### 환경 변수 (Environment Variables)

```bash
export ONEERP_DEBUG=true
export ONEERP_FERRETDB_URI=mongodb://localhost:27017
export ONEERP_DATABASE_NAME=oneerp_dev
```

---

## Step 1: 자산 등록 (Register Asset)

고정자산 (Fixed Asset)을 등록한다.
취득원가 (Gross Amount), 잔존가치 (Salvage Value), 내용연수 (Useful Life), 상각 방법 (Depreciation Method)을 설정한다.

```bash
curl -s -X POST http://localhost:8010/api/v1/assets \
  -H "Content-Type: application/json" \
  -d '{
    "asset_name": "업무용 노트북 (Dell Latitude 5550)",
    "asset_category": "IT장비",
    "purchase_date": "2026-01-15",
    "gross_amount": 2400000,
    "salvage_value": 240000,
    "current_value": 2400000,
    "useful_life_years": 4,
    "depreciation_method": "straight_line",
    "location": "본사 3층 개발팀",
    "status": "submitted"
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "_id": "AST-0001",
  "asset_name": "업무용 노트북 (Dell Latitude 5550)",
  "gross_amount": 2400000,
  "current_value": 2400000,
  "useful_life_years": 4,
  "depreciation_method": "straight_line"
}
```

---

## Step 2: 감가상각 스케줄 미리보기 (Preview Depreciation Schedule)

`DepreciationService.get_depreciation_schedule()` — 전체 기간 감가상각 스케줄을 미리 확인한다.

```bash
curl -s "http://localhost:8010/api/v1/assets/AST-0001/depreciation-schedule" | jq
```

### 기대 결과 (Expected Result)

정액법 (Straight-Line Method) 계산:
- 월 상각액 = (취득원가 - 잔존가치) / (내용연수 x 12)
- = (2,400,000 - 240,000) / (4 x 12) = **45,000원/월**

```json
[
  {"month": 1, "depreciation_amount": 45000, "accumulated_depreciation": 45000, "remaining_value": 2355000},
  {"month": 2, "depreciation_amount": 45000, "accumulated_depreciation": 90000, "remaining_value": 2310000},
  "..."
]
```

---

## Step 3: 월별 감가상각 실행 (Run Monthly Depreciation)

`DepreciationService.run_monthly_depreciation()` — 전체 active 자산에 대해 월별 일괄 상각을 실행한다.
DepreciationEntry를 생성하고 current_value를 차감한다.

```bash
# 2026년 2월 상각 실행 (Run depreciation for Feb 2026)
curl -s -X POST http://localhost:8010/api/v1/depreciation/run \
  -H "Content-Type: application/json" \
  -d '{"year_month": "2026-02"}' | jq
```

### 기대 결과 (Expected Result)

```json
[
  {
    "entry_id": "DEP-0001",
    "asset_id": "AST-0001",
    "depreciation_amount": 45000,
    "remaining_value": 2355000
  }
]
```

자산의 current_value가 2,400,000 -> 2,355,000으로 차감된다.

### 연속 상각 (Run Consecutive Months)

```bash
# 3월 상각 (March)
curl -s -X POST http://localhost:8010/api/v1/depreciation/run \
  -H "Content-Type: application/json" \
  -d '{"year_month": "2026-03"}' | jq
# remaining_value: 2,310,000 (2,355,000 - 45,000)
```

**회계 분개 (Accounting Journal Entry):**

| 구분 (Type) | 계정 (Account) | 차변 (Debit) | 대변 (Credit) |
|-------------|---------------|-------------|--------------|
| 차변 | 감가상각비 (Depreciation Expense) | 45,000 | - |
| 대변 | 감가상각누계액 (Accumulated Depreciation) | - | 45,000 |

---

## Step 4: 자산 이동 (Transfer Asset)

`AssetLifecycleService.move_asset()` — 자산을 다른 위치로 이동한다.
AssetMovement 기록이 생성된다.

```bash
curl -s -X POST http://localhost:8010/api/v1/assets/AST-0001/move \
  -H "Content-Type: application/json" \
  -d '{
    "from_location": "본사 3층 개발팀",
    "to_location": "본사 5층 인프라팀",
    "movement_date": "2026-03-15"
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "movement_id": "AMOV-0001",
  "asset_id": "AST-0001",
  "from_location": "본사 3층 개발팀",
  "to_location": "본사 5층 인프라팀"
}
```

---

## Step 5: 자산 재평가 (Revalue Asset)

`AssetLifecycleService.revalue_asset()` — 자산의 공정가치 (Fair Value)가 변동되었을 때
장부가를 재평가한다.

```bash
curl -s -X POST http://localhost:8010/api/v1/assets/AST-0001/revalue \
  -H "Content-Type: application/json" \
  -d '{
    "new_value": 2200000,
    "revaluation_date": "2026-03-20"
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "revaluation_id": "ARVAL-0001",
  "asset_id": "AST-0001",
  "old_value": 2310000,
  "new_value": 2200000,
  "difference": -110000
}
```

차액 -110,000원은 재평가손실 (Revaluation Loss)로 회계 처리된다.

---

## Step 6: 자산 처분 (Dispose Asset)

`AssetLifecycleService.dispose_asset()` — 자산을 매각 (Sale) 또는 폐기 (Scrap)한다.
처분손익 = 매각금액 - 장부가. 자산 상태가 `scrapped`로 변경된다.

```bash
curl -s -X POST http://localhost:8010/api/v1/assets/AST-0001/dispose \
  -H "Content-Type: application/json" \
  -d '{
    "disposal_method": "sale",
    "sale_amount": 1800000,
    "disposal_date": "2028-01-15"
  }' | jq
```

### 기대 결과 (Expected Result)

```json
{
  "disposal_id": "ADSP-0001",
  "asset_id": "AST-0001",
  "disposal_method": "sale",
  "book_value": 2200000,
  "sale_amount": 1800000,
  "gain_loss": -400000
}
```

처분손실 (Disposal Loss): 1,800,000 - 2,200,000 = **-400,000원**

**회계 분개 (Accounting Journal Entry):**

| 구분 (Type) | 계정 (Account) | 차변 (Debit) | 대변 (Credit) |
|-------------|---------------|-------------|--------------|
| 차변 | 현금/은행 (Cash/Bank) | 1,800,000 | - |
| 차변 | 감가상각누계액 (Accum. Depreciation) | 200,000 | - |
| 차변 | 유형자산처분손실 (Disposal Loss) | 400,000 | - |
| 대변 | 유형자산 (Fixed Asset) | - | 2,400,000 |

---

## 검증 (Verification)

### 1. 자산 이력 조회 (View Asset History)

`AssetLifecycleService.get_asset_history()` — 이동/처분/재평가/상각 통합 이력을 조회한다.

```bash
curl -s "http://localhost:8010/api/v1/assets/AST-0001/history" | jq
```

### 2. 상각 항목 확인 (Verify Depreciation Entries)

```bash
curl -s "http://localhost:8010/api/v1/depreciation-entries?asset=AST-0001" | jq
# 2건 확인 (2월, 3월)
```

### 3. 자산 상태 확인 (Verify Asset Status)

```bash
curl -s "http://localhost:8010/api/v1/assets/AST-0001" | jq '.status'
# 기대값 (Expected): "scrapped"
```

---

## 정률법 상각 시나리오 (Declining Balance Method Scenario)

정률법 (Declining Balance)을 사용하는 자산의 예:

```bash
curl -s -X POST http://localhost:8010/api/v1/assets \
  -H "Content-Type: application/json" \
  -d '{
    "asset_name": "CNC 선반 (Doosan Lynx 2100)",
    "asset_category": "생산설비",
    "purchase_date": "2026-01-01",
    "gross_amount": 80000000,
    "salvage_value": 8000000,
    "current_value": 80000000,
    "useful_life_years": 10,
    "depreciation_method": "declining_balance",
    "location": "제1공장",
    "status": "submitted"
  }' | jq
```

정률법 계산:
- rate = 1 - (잔존가치/취득원가)^(1/내용연수) = 1 - (8M/80M)^(1/10) = 약 0.2056
- 1월 상각: 80,000,000 x 0.2056 / 12 = **약 1,370,667원**

매월 상각액이 체감한다 — 초기에 더 많이 상각하는 가속상각법 (Accelerated Depreciation).

---

## 전체 흐름 다이어그램 (Flow Diagram)

```
[Assets]                                    [Accounting]
    |                                           |
  1. 자산 등록 (Register)                        |
     gross_amount, salvage, useful_life         |
    |                                           |
  2. 상각 스케줄 미리보기                         |
     Preview Depreciation Schedule              |
    |                                           |
  3. 월별 상각 실행 --------------------------> 상각 분개
     Run Monthly Depreciation                   Depreciation JE
     current_value -= dep_amount            (Dr: 감가상각비 / Cr: 감가상각누계)
    |                                           |
  4. 자산 이동 (부서 간 Transfer)                 |
     AssetMovement 기록                          |
    |                                           |
  5. 자산 재평가 (Revaluation)                    |
     current_value 변경 ----------------------> 재평가 분개
    |                                           Revaluation JE
    |                                           |
  6. 자산 처분 (Sale/Scrap) ------------------> 처분 분개
     status -> scrapped                         Disposal JE
     gain_loss = sale - book_value          (Dr: Cash+AccumDep+Loss /
    |                                        Cr: Fixed Asset)
```

---

## 정리 (Summary)

이 튜토리얼에서 배운 내용:
- 고정자산 (Fixed Asset) 등록과 감가상각 설정
- 정액법 (Straight-Line) vs 정률법 (Declining Balance) 감가상각 계산
- 잔존가치 (Salvage Value) 보호 — 장부가가 잔존가치 이하로 떨어지지 않도록 조정
- 자산 이동 (Movement), 재평가 (Revaluation), 처분 (Disposal) 흐름
- 처분손익 (Gain/Loss on Disposal) = 매각금액 - 장부가
- `get_asset_history()` 통합 이력 조회
