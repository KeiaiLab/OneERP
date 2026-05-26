"""Payroll 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

10개 엔티티를 EntityMeta로 선언한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.additional_salary import (
    AdditionalSalary,
    AdditionalSalaryCreate,
    AdditionalSalaryUpdate,
)
from .models.employee_advance import (
    EmployeeAdvance,
    EmployeeAdvanceCreate,
    EmployeeAdvanceUpdate,
)
from .models.employee_benefit_claim import (
    EmployeeBenefitClaim,
    EmployeeBenefitClaimCreate,
    EmployeeBenefitClaimUpdate,
)
from .models.employee_benefit_plan import (
    EmployeeBenefitPlan,
    EmployeeBenefitPlanCreate,
    EmployeeBenefitPlanUpdate,
)
from .models.employee_incentive import (
    EmployeeIncentive,
    EmployeeIncentiveCreate,
    EmployeeIncentiveUpdate,
)
from .models.employee_loan import (
    EmployeeLoan,
    EmployeeLoanCreate,
    EmployeeLoanUpdate,
)
from .models.employee_tax_exemption import (
    EmployeeTaxExemption,
    EmployeeTaxExemptionCreate,
    EmployeeTaxExemptionUpdate,
)
from .models.korean_payroll_adjustment import (
    KoreanPayrollAdjustment,
    KoreanPayrollAdjustmentCreate,
    KoreanPayrollAdjustmentUpdate,
)
from .models.retention_bonus import (
    RetentionBonus,
    RetentionBonusCreate,
    RetentionBonusUpdate,
)
from .models.salary_revision import (
    SalaryRevision,
    SalaryRevisionCreate,
    SalaryRevisionUpdate,
)

# --- 마스터 데이터 ---

EMPLOYEE_BENEFIT_PLAN = EntityMeta(
    collection="employee_benefit_plans",
    prefix="EBPL",
    api_path="/api/v1/employee-benefit-plans",
    tag="복리후생플랜",
    resource="employee_benefit_plan",
    model=EmployeeBenefitPlan,
    create_schema=EmployeeBenefitPlanCreate,
    update_schema=EmployeeBenefitPlanUpdate,
    archetype="master",
    not_found_message="직원 복리후생 플랜을 찾을 수 없습니다",
)

# --- 트랜잭션 문서 ---

ADDITIONAL_SALARY = EntityMeta(
    collection="additional_salaries",
    prefix="ASAL",
    api_path="/api/v1/additional-salaries",
    tag="추가급여",
    resource="additional_salary",
    model=AdditionalSalary,
    create_schema=AdditionalSalaryCreate,
    update_schema=AdditionalSalaryUpdate,
    archetype="transaction",
    not_found_message="추가 급여를 찾을 수 없습니다",
)

EMPLOYEE_TAX_EXEMPTION = EntityMeta(
    collection="employee_tax_exemptions",
    prefix="ETXE",
    api_path="/api/v1/employee-tax-exemptions",
    tag="세금면제",
    resource="employee_tax_exemption",
    model=EmployeeTaxExemption,
    create_schema=EmployeeTaxExemptionCreate,
    update_schema=EmployeeTaxExemptionUpdate,
    archetype="transaction",
    not_found_message="직원 세금 면제를 찾을 수 없습니다",
)

EMPLOYEE_ADVANCE = EntityMeta(
    collection="employee_advances",
    prefix="EADV",
    api_path="/api/v1/employee-advances",
    tag="직원선지급",
    resource="employee_advance",
    model=EmployeeAdvance,
    create_schema=EmployeeAdvanceCreate,
    update_schema=EmployeeAdvanceUpdate,
    archetype="transaction",
    not_found_message="직원 선지급을 찾을 수 없습니다",
)

EMPLOYEE_LOAN = EntityMeta(
    collection="employee_loans",
    prefix="ELOAN",
    api_path="/api/v1/employee-loans",
    tag="직원대출",
    resource="employee_loan",
    model=EmployeeLoan,
    create_schema=EmployeeLoanCreate,
    update_schema=EmployeeLoanUpdate,
    archetype="transaction",
    not_found_message="직원 대출을 찾을 수 없습니다",
)

EMPLOYEE_BENEFIT_CLAIM = EntityMeta(
    collection="employee_benefit_claims",
    prefix="EBCL",
    api_path="/api/v1/employee-benefit-claims",
    tag="복리후생청구",
    resource="employee_benefit_claim",
    model=EmployeeBenefitClaim,
    create_schema=EmployeeBenefitClaimCreate,
    update_schema=EmployeeBenefitClaimUpdate,
    archetype="transaction",
    not_found_message="직원 복리후생 청구를 찾을 수 없습니다",
)

RETENTION_BONUS = EntityMeta(
    collection="retention_bonuses",
    prefix="RETB",
    api_path="/api/v1/retention-bonuses",
    tag="리텐션보너스",
    resource="retention_bonus",
    model=RetentionBonus,
    create_schema=RetentionBonusCreate,
    update_schema=RetentionBonusUpdate,
    archetype="transaction",
    not_found_message="리텐션 보너스를 찾을 수 없습니다",
)

EMPLOYEE_INCENTIVE = EntityMeta(
    collection="employee_incentives",
    prefix="EINC",
    api_path="/api/v1/employee-incentives",
    tag="직원인센티브",
    resource="employee_incentive",
    model=EmployeeIncentive,
    create_schema=EmployeeIncentiveCreate,
    update_schema=EmployeeIncentiveUpdate,
    archetype="transaction",
    not_found_message="직원 인센티브를 찾을 수 없습니다",
)

SALARY_REVISION = EntityMeta(
    collection="salary_revisions",
    prefix="SLRV",
    api_path="/api/v1/salary-revisions",
    tag="급여조정",
    resource="salary_revision",
    model=SalaryRevision,
    create_schema=SalaryRevisionCreate,
    update_schema=SalaryRevisionUpdate,
    archetype="transaction",
    not_found_message="급여 조정을 찾을 수 없습니다",
)

KOREAN_PAYROLL_ADJUSTMENT = EntityMeta(
    collection="korean_payroll_adjustments",
    prefix="KPADJ",
    api_path="/api/v1/korean-payroll-adjustments",
    tag="한국급여조정",
    resource="korean_payroll_adjustment",
    model=KoreanPayrollAdjustment,
    create_schema=KoreanPayrollAdjustmentCreate,
    update_schema=KoreanPayrollAdjustmentUpdate,
    archetype="transaction",
    not_found_message="한국 급여 조정을 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    EMPLOYEE_BENEFIT_PLAN,
    # 트랜잭션
    ADDITIONAL_SALARY,
    EMPLOYEE_TAX_EXEMPTION,
    EMPLOYEE_ADVANCE,
    EMPLOYEE_LOAN,
    EMPLOYEE_BENEFIT_CLAIM,
    RETENTION_BONUS,
    EMPLOYEE_INCENTIVE,
    SALARY_REVISION,
    KOREAN_PAYROLL_ADJUSTMENT,
]
