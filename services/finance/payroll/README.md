# OneERP Payroll 서비스 (Payroll Service)

> 급여 구조, 급여 처리, 4대보험, 원천징수, 연말정산 등 급여 관리를 담당하는 서비스 / Manages payroll including salary structures, payroll processing, social insurance, withholding tax, and year-end settlement

## 도메인 개요 (Domain Overview)

Payroll 서비스는 급여 구조 (Salary Structure) 설계, 급여 항목 (Salary Component) 관리, 급여 명세서 (Salary Slip) 생성, 4대보험 (Social Insurance) 관리, 원천징수세 (Withholding Tax) 계산, 연말정산 (Year-End Settlement), 퇴직금 (Retirement Pay) 처리 등 한국 노동법에 맞는 급여 업무 전반을 담당한다. 추가급여 (Additional Salary), 인센티브 (Incentive), 직원대출/선지급 (Employee Loan/Advance), 복리후생 청구 (Benefit Claim)도 관리한다.

## 기술 스택 (Tech Stack)

| 항목 (Item) | 기술 (Technology) |
|-------------|-------------------|
| 프레임워크 (Framework) | FastAPI + Pydantic v2 |
| 데이터베이스 (Database) | FerretDB (MongoDB Protocol) |
| 포트 (Port) | 8007 |

## 엔티티 (Entities) — 19개

### 마스터 데이터 (Master Data)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| EmployeeBenefitPlan | employee_benefit_plans | 복리후생플랜 (Employee Benefit Plan) |

### 트랜잭션 문서 (Transaction Documents)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| AdditionalSalary | additional_salaries | 추가급여 (Additional Salary) |
| EmployeeTaxExemption | employee_tax_exemptions | 세금면제 (Employee Tax Exemption) |
| EmployeeAdvance | employee_advances | 직원선지급 (Employee Advance) |
| EmployeeLoan | employee_loans | 직원대출 (Employee Loan) |
| EmployeeBenefitClaim | employee_benefit_claims | 복리후생청구 (Employee Benefit Claim) |
| RetentionBonus | retention_bonuses | 리텐션보너스 (Retention Bonus) |
| EmployeeIncentive | employee_incentives | 직원인센티브 (Employee Incentive) |
| SalaryRevision | salary_revisions | 급여조정 (Salary Revision) |
| KoreanPayrollAdjustment | korean_payroll_adjustments | 한국급여조정 (Korean Payroll Adjustment) |

## 비즈니스 로직 (Business Logic)

| 서비스 (Service) | 주요 메서드 (Key Methods) | 설명 (Description) |
|-----------------|-------------------------|-------------------|
| PayrollCalculationService | 급여 계산, 공제 적용 | 급여 명세서 생성 엔진 (Payroll Calculation Engine) |
| SocialInsuranceService | 4대보험 요율 적용, 산출 | 국민연금/건보/고용/산재 (Social Insurance) |
| IncomeTaxService | 소득세 계산, 원천징수 | 근로소득세 계산 (Income Tax Calculation) |
| YearEndSettlementService | 연말정산 처리 | 소득공제/세액공제 계산 (Year-End Settlement) |
| InsuranceRates | 보험 요율 관리 | 4대보험 요율표 (Insurance Rate Table) |

## API 엔드포인트 (API Endpoints)

### 자동 생성 CRUD (Auto-generated CRUD)
EntityMeta 기반 10개 엔드포인트 자동 생성 (Auto-generated from EntityMeta)

### 커스텀 라우트 (Custom Routes)
| 메서드 (Method) | 경로 (Path) | 설명 (Description) |
|----------------|-------------|-------------------|
| CRUD | /api/v1/salary-structures | 급여 구조 관리 (Salary Structures) |
| CRUD | /api/v1/salary-slips | 급여 명세서 관리 (Salary Slips) |
| CRUD | /api/v1/salary-components | 급여 항목 관리 (Salary Components) |
| CRUD | /api/v1/payroll-entries | 급여 처리 일괄 (Payroll Entries) |
| CRUD | /api/v1/social-insurances | 4대보험 관리 (Social Insurance) |
| CRUD | /api/v1/withholding-taxes | 원천징수 관리 (Withholding Tax) |
| CRUD | /api/v1/year-end-settlements | 연말정산 관리 (Year-End Settlement) |
| CRUD | /api/v1/retirement-pays | 퇴직금 처리 (Retirement Pay) |
| CRUD | /api/v1/payroll-tax-returns | 급여 세금 신고 (Payroll Tax Returns) |

## 이벤트 (Events)

### 구독 (Subscribed)
| EventType | 핸들러 (Handler) |
|-----------|-----------------|
| 급여 관련 이벤트 (Payroll Events) | events/handlers.py |

## 실행 방법 (How to Run)

```bash
uv run --package oneerp-payroll --directory services/payroll uvicorn app.main:app --port 8007
```

## 테스트 (Testing)

```bash
uv run pytest services/payroll/ -m "not integration and not e2e" -v
```
