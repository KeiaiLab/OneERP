"""HR 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

41개 엔티티를 EntityMeta로 선언한다.
커스텀 로직이 있는 엔티티(부서/직급/휴가유형/휴가신청/휴가잔액/근태)는
routes/ 디렉토리에서 직접 관리한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.appraisal import Appraisal, AppraisalCreate, AppraisalUpdate
from .models.appraisal_cycle import (
    AppraisalCycle,
    AppraisalCycleCreate,
    AppraisalCycleUpdate,
)
from .models.appraisal_template import (
    AppraisalTemplate,
    AppraisalTemplateCreate,
    AppraisalTemplateUpdate,
)
from .models.attendance import Attendance, AttendanceCreate, AttendanceUpdate
from .models.compensatory_leave_request import (
    CompensatoryLeaveRequest,
    CompensatoryLeaveRequestCreate,
    CompensatoryLeaveRequestUpdate,
)
from .models.competency_framework import (
    CompetencyFramework,
    CompetencyFrameworkCreate,
    CompetencyFrameworkUpdate,
)
from .models.designation import Designation, DesignationCreate, DesignationUpdate
from .models.employee_document_expiry import (
    EmployeeDocumentExpiry,
    EmployeeDocumentExpiryCreate,
    EmployeeDocumentExpiryUpdate,
)
from .models.employee_engagement_survey import (
    EmployeeEngagementSurvey,
    EmployeeEngagementSurveyCreate,
    EmployeeEngagementSurveyUpdate,
)
from .models.employee_group import (
    EmployeeGroup,
    EmployeeGroupCreate,
    EmployeeGroupUpdate,
)
from .models.employee_offboarding import (
    EmployeeOffboarding,
    EmployeeOffboardingCreate,
    EmployeeOffboardingUpdate,
)
from .models.employee_onboarding import (
    EmployeeOnboarding,
    EmployeeOnboardingCreate,
    EmployeeOnboardingUpdate,
)
from .models.employee_referral import (
    EmployeeReferral,
    EmployeeReferralCreate,
    EmployeeReferralUpdate,
)
from .models.employee_skill_map import (
    EmployeeSkillMap,
    EmployeeSkillMapCreate,
    EmployeeSkillMapUpdate,
)
from .models.employee_transfer import (
    EmployeeTransfer,
    EmployeeTransferCreate,
    EmployeeTransferUpdate,
)
from .models.goal_setting import GoalSetting, GoalSettingCreate, GoalSettingUpdate
from .models.health_checkup import (
    HealthCheckup,
    HealthCheckupCreate,
    HealthCheckupUpdate,
)
from .models.interview_feedback import (
    InterviewFeedback,
    InterviewFeedbackCreate,
    InterviewFeedbackUpdate,
)
from .models.interview_round import (
    InterviewRound,
    InterviewRoundCreate,
    InterviewRoundUpdate,
)
from .models.job_applicant import (
    JobApplicant,
    JobApplicantCreate,
    JobApplicantUpdate,
)
from .models.job_opening import JobOpening, JobOpeningCreate, JobOpeningUpdate
from .models.learning_certification import (
    LearningCertification,
    LearningCertificationCreate,
    LearningCertificationUpdate,
)
from .models.learning_course import (
    LearningCourse,
    LearningCourseCreate,
    LearningCourseUpdate,
)
from .models.learning_enrollment import (
    LearningEnrollment,
    LearningEnrollmentCreate,
    LearningEnrollmentUpdate,
)
from .models.leave_period import LeavePeriod, LeavePeriodCreate, LeavePeriodUpdate
from .models.leave_policy import LeavePolicy, LeavePolicyCreate, LeavePolicyUpdate
from .models.leave_policy_assignment import (
    LeavePolicyAssignment,
    LeavePolicyAssignmentCreate,
    LeavePolicyAssignmentUpdate,
)
from .models.leave_type import LeaveType, LeaveTypeCreate, LeaveTypeUpdate
from .models.offer_letter import OfferLetter, OfferLetterCreate, OfferLetterUpdate
from .models.overtime_entry import (
    OvertimeEntry,
    OvertimeEntryCreate,
    OvertimeEntryUpdate,
)
from .models.overtime_policy import (
    OvertimePolicy,
    OvertimePolicyCreate,
    OvertimePolicyUpdate,
)
from .models.safety_incident import (
    SafetyIncident,
    SafetyIncidentCreate,
    SafetyIncidentUpdate,
)
from .models.safety_training import (
    SafetyTraining,
    SafetyTrainingCreate,
    SafetyTrainingUpdate,
)
from .models.shift_assignment import (
    ShiftAssignment,
    ShiftAssignmentCreate,
    ShiftAssignmentUpdate,
)
from .models.shift_request import (
    ShiftRequest,
    ShiftRequestCreate,
    ShiftRequestUpdate,
)
from .models.shift_type import ShiftType, ShiftTypeCreate, ShiftTypeUpdate
from .models.succession_plan import (
    SuccessionPlan,
    SuccessionPlanCreate,
    SuccessionPlanUpdate,
)
from .models.talent_development_plan import (
    TalentDevelopmentPlan,
    TalentDevelopmentPlanCreate,
    TalentDevelopmentPlanUpdate,
)
from .models.training_event import (
    TrainingEvent,
    TrainingEventCreate,
    TrainingEventUpdate,
)

# --- 마스터 데이터 ---

DESIGNATION = EntityMeta(
    collection="designations",
    prefix="DESG",
    api_path="/api/v1/designations",
    tag="직위",
    resource="designation",
    model=Designation,
    create_schema=DesignationCreate,
    update_schema=DesignationUpdate,
    archetype="master",
    not_found_message="직위를 찾을 수 없습니다",
)

LEAVE_TYPE = EntityMeta(
    collection="leave_types",
    prefix="LT",
    api_path="/api/v1/leave-types",
    tag="휴가유형",
    resource="leave_type",
    model=LeaveType,
    create_schema=LeaveTypeCreate,
    update_schema=LeaveTypeUpdate,
    archetype="master",
    not_found_message="휴가유형을 찾을 수 없습니다",
)

EMPLOYEE_SKILL_MAP = EntityMeta(
    collection="employee_skill_maps",
    prefix="ESM",
    api_path="/api/v1/employee-skill-maps",
    tag="직원역량맵",
    resource="employee_skill_map",
    model=EmployeeSkillMap,
    create_schema=EmployeeSkillMapCreate,
    update_schema=EmployeeSkillMapUpdate,
    archetype="master",
    not_found_message="직원역량맵을 찾을 수 없습니다",
)

SHIFT_TYPE = EntityMeta(
    collection="shift_types",
    prefix="SHFT",
    api_path="/api/v1/shift-types",
    tag="교대유형",
    resource="shift_type",
    model=ShiftType,
    create_schema=ShiftTypeCreate,
    update_schema=ShiftTypeUpdate,
    archetype="master",
    not_found_message="교대유형을 찾을 수 없습니다",
)

OVERTIME_POLICY = EntityMeta(
    collection="overtime_policies",
    prefix="OTP",
    api_path="/api/v1/overtime-policies",
    tag="초과근무정책",
    resource="overtime_policy",
    model=OvertimePolicy,
    create_schema=OvertimePolicyCreate,
    update_schema=OvertimePolicyUpdate,
    archetype="master",
    not_found_message="초과근무 정책을 찾을 수 없습니다",
)

EMPLOYEE_GROUP = EntityMeta(
    collection="employee_groups",
    prefix="EGRP",
    api_path="/api/v1/employee-groups",
    tag="직원그룹",
    resource="employee_group",
    model=EmployeeGroup,
    create_schema=EmployeeGroupCreate,
    update_schema=EmployeeGroupUpdate,
    archetype="master",
    not_found_message="직원 그룹을 찾을 수 없습니다",
)

LEAVE_POLICY = EntityMeta(
    collection="leave_policies",
    prefix="LVPL",
    api_path="/api/v1/leave-policies",
    tag="휴가정책",
    resource="leave_policy",
    model=LeavePolicy,
    create_schema=LeavePolicyCreate,
    update_schema=LeavePolicyUpdate,
    archetype="master",
    not_found_message="휴가 정책을 찾을 수 없습니다",
)

LEAVE_PERIOD = EntityMeta(
    collection="leave_periods",
    prefix="LVPD",
    api_path="/api/v1/leave-periods",
    tag="휴가기간",
    resource="leave_period",
    model=LeavePeriod,
    create_schema=LeavePeriodCreate,
    update_schema=LeavePeriodUpdate,
    archetype="master",
    not_found_message="휴가 기간을 찾을 수 없습니다",
)

APPRAISAL_TEMPLATE = EntityMeta(
    collection="appraisal_templates",
    prefix="APRT",
    api_path="/api/v1/appraisal-templates",
    tag="평가템플릿",
    resource="appraisal_template",
    model=AppraisalTemplate,
    create_schema=AppraisalTemplateCreate,
    update_schema=AppraisalTemplateUpdate,
    archetype="master",
    not_found_message="인사 평가 템플릿을 찾을 수 없습니다",
)

LEARNING_COURSE = EntityMeta(
    collection="learning_courses",
    prefix="LCRSE",
    api_path="/api/v1/learning-courses",
    tag="학습과정",
    resource="learning_course",
    model=LearningCourse,
    create_schema=LearningCourseCreate,
    update_schema=LearningCourseUpdate,
    archetype="master",
    not_found_message="학습 과정을 찾을 수 없습니다",
)

COMPETENCY_FRAMEWORK = EntityMeta(
    collection="competency_frameworks",
    prefix="CMPF",
    api_path="/api/v1/competency-frameworks",
    tag="역량프레임워크",
    resource="competency_framework",
    model=CompetencyFramework,
    create_schema=CompetencyFrameworkCreate,
    update_schema=CompetencyFrameworkUpdate,
    archetype="master",
    not_found_message="역량 프레임워크를 찾을 수 없습니다",
)

# --- 트랜잭션 문서 ---

ATTENDANCE = EntityMeta(
    collection="attendances",
    prefix="ATT",
    api_path="/api/v1/attendances",
    tag="출퇴근",
    resource="attendance",
    model=Attendance,
    create_schema=AttendanceCreate,
    update_schema=AttendanceUpdate,
    archetype="transaction",
    not_found_message="출퇴근 기록을 찾을 수 없습니다",
)

EMPLOYEE_TRANSFER = EntityMeta(
    collection="employee_transfers",
    prefix="ETR",
    api_path="/api/v1/employee-transfers",
    tag="인사이동",
    resource="employee_transfer",
    model=EmployeeTransfer,
    create_schema=EmployeeTransferCreate,
    update_schema=EmployeeTransferUpdate,
    archetype="transaction",
    not_found_message="인사이동을 찾을 수 없습니다",
)

SHIFT_ASSIGNMENT = EntityMeta(
    collection="shift_assignments",
    prefix="SA",
    api_path="/api/v1/shift-assignments",
    tag="교대배정",
    resource="shift_assignment",
    model=ShiftAssignment,
    create_schema=ShiftAssignmentCreate,
    update_schema=ShiftAssignmentUpdate,
    archetype="transaction",
    not_found_message="교대배정을 찾을 수 없습니다",
)

EMPLOYEE_ONBOARDING = EntityMeta(
    collection="employee_onboardings",
    prefix="EON",
    api_path="/api/v1/employee-onboardings",
    tag="입사절차",
    resource="employee_onboarding",
    model=EmployeeOnboarding,
    create_schema=EmployeeOnboardingCreate,
    update_schema=EmployeeOnboardingUpdate,
    archetype="transaction",
    not_found_message="입사절차를 찾을 수 없습니다",
)

EMPLOYEE_OFFBOARDING = EntityMeta(
    collection="employee_offboardings",
    prefix="EOFF",
    api_path="/api/v1/employee-offboardings",
    tag="퇴사절차",
    resource="employee_offboarding",
    model=EmployeeOffboarding,
    create_schema=EmployeeOffboardingCreate,
    update_schema=EmployeeOffboardingUpdate,
    archetype="transaction",
    not_found_message="퇴사절차를 찾을 수 없습니다",
)

JOB_OPENING = EntityMeta(
    collection="job_openings",
    prefix="JOPN",
    api_path="/api/v1/job-openings",
    tag="채용공고",
    resource="job_opening",
    model=JobOpening,
    create_schema=JobOpeningCreate,
    update_schema=JobOpeningUpdate,
    archetype="transaction",
    not_found_message="채용 공고를 찾을 수 없습니다",
)

JOB_APPLICANT = EntityMeta(
    collection="job_applicants",
    prefix="JAPP",
    api_path="/api/v1/job-applicants",
    tag="입사지원자",
    resource="job_applicant",
    model=JobApplicant,
    create_schema=JobApplicantCreate,
    update_schema=JobApplicantUpdate,
    archetype="transaction",
    not_found_message="입사 지원자를 찾을 수 없습니다",
)

OFFER_LETTER = EntityMeta(
    collection="offer_letters",
    prefix="OFLT",
    api_path="/api/v1/offer-letters",
    tag="채용제안서",
    resource="offer_letter",
    model=OfferLetter,
    create_schema=OfferLetterCreate,
    update_schema=OfferLetterUpdate,
    archetype="transaction",
    not_found_message="채용 제안서를 찾을 수 없습니다",
)

INTERVIEW_ROUND = EntityMeta(
    collection="interview_rounds",
    prefix="INTR",
    api_path="/api/v1/interview-rounds",
    tag="면접라운드",
    resource="interview_round",
    model=InterviewRound,
    create_schema=InterviewRoundCreate,
    update_schema=InterviewRoundUpdate,
    archetype="transaction",
    not_found_message="면접 라운드를 찾을 수 없습니다",
)

INTERVIEW_FEEDBACK = EntityMeta(
    collection="interview_feedbacks",
    prefix="INTFB",
    api_path="/api/v1/interview-feedbacks",
    tag="면접피드백",
    resource="interview_feedback",
    model=InterviewFeedback,
    create_schema=InterviewFeedbackCreate,
    update_schema=InterviewFeedbackUpdate,
    archetype="transaction",
    not_found_message="면접 피드백을 찾을 수 없습니다",
)

LEAVE_POLICY_ASSIGNMENT = EntityMeta(
    collection="leave_policy_assignments",
    prefix="LVPA",
    api_path="/api/v1/leave-policy-assignments",
    tag="휴가정책할당",
    resource="leave_policy_assignment",
    model=LeavePolicyAssignment,
    create_schema=LeavePolicyAssignmentCreate,
    update_schema=LeavePolicyAssignmentUpdate,
    archetype="transaction",
    not_found_message="휴가 정책 할당을 찾을 수 없습니다",
)

COMPENSATORY_LEAVE_REQUEST = EntityMeta(
    collection="compensatory_leave_requests",
    prefix="CLVR",
    api_path="/api/v1/compensatory-leave-requests",
    tag="대체휴가신청",
    resource="compensatory_leave_request",
    model=CompensatoryLeaveRequest,
    create_schema=CompensatoryLeaveRequestCreate,
    update_schema=CompensatoryLeaveRequestUpdate,
    archetype="transaction",
    not_found_message="대체 휴가 신청을 찾을 수 없습니다",
)

SHIFT_REQUEST = EntityMeta(
    collection="shift_requests",
    prefix="SHRQ",
    api_path="/api/v1/shift-requests",
    tag="교대변경요청",
    resource="shift_request",
    model=ShiftRequest,
    create_schema=ShiftRequestCreate,
    update_schema=ShiftRequestUpdate,
    archetype="transaction",
    not_found_message="교대 변경 요청을 찾을 수 없습니다",
)

OVERTIME_ENTRY = EntityMeta(
    collection="overtime_entries",
    prefix="OTE",
    api_path="/api/v1/overtime-entries",
    tag="초과근무기록",
    resource="overtime_entry",
    model=OvertimeEntry,
    create_schema=OvertimeEntryCreate,
    update_schema=OvertimeEntryUpdate,
    archetype="transaction",
    not_found_message="초과근무 기록을 찾을 수 없습니다",
)

EMPLOYEE_REFERRAL = EntityMeta(
    collection="employee_referrals",
    prefix="EREF",
    api_path="/api/v1/employee-referrals",
    tag="직원추천채용",
    resource="employee_referral",
    model=EmployeeReferral,
    create_schema=EmployeeReferralCreate,
    update_schema=EmployeeReferralUpdate,
    archetype="transaction",
    not_found_message="직원 추천 채용을 찾을 수 없습니다",
)

EMPLOYEE_DOCUMENT_EXPIRY = EntityMeta(
    collection="employee_document_expiries",
    prefix="EDEX",
    api_path="/api/v1/employee-document-expiries",
    tag="직원서류만료",
    resource="employee_document_expiry",
    model=EmployeeDocumentExpiry,
    create_schema=EmployeeDocumentExpiryCreate,
    update_schema=EmployeeDocumentExpiryUpdate,
    archetype="transaction",
    not_found_message="직원 서류 만료를 찾을 수 없습니다",
)

TRAINING_EVENT = EntityMeta(
    collection="training_events",
    prefix="TREV",
    api_path="/api/v1/training-events",
    tag="교육이벤트",
    resource="training_event",
    model=TrainingEvent,
    create_schema=TrainingEventCreate,
    update_schema=TrainingEventUpdate,
    archetype="transaction",
    not_found_message="교육 이벤트를 찾을 수 없습니다",
)

APPRAISAL_CYCLE = EntityMeta(
    collection="appraisal_cycles",
    prefix="APRC",
    api_path="/api/v1/appraisal-cycles",
    tag="평가주기",
    resource="appraisal_cycle",
    model=AppraisalCycle,
    create_schema=AppraisalCycleCreate,
    update_schema=AppraisalCycleUpdate,
    archetype="transaction",
    not_found_message="인사 평가 주기를 찾을 수 없습니다",
)

APPRAISAL = EntityMeta(
    collection="appraisals",
    prefix="APR",
    api_path="/api/v1/appraisals",
    tag="인사평가",
    resource="appraisal",
    model=Appraisal,
    create_schema=AppraisalCreate,
    update_schema=AppraisalUpdate,
    archetype="transaction",
    not_found_message="인사 평가를 찾을 수 없습니다",
)

GOAL_SETTING = EntityMeta(
    collection="goal_settings",
    prefix="GOAL",
    api_path="/api/v1/goal-settings",
    tag="목표설정",
    resource="goal_setting",
    model=GoalSetting,
    create_schema=GoalSettingCreate,
    update_schema=GoalSettingUpdate,
    archetype="transaction",
    not_found_message="목표 설정을 찾을 수 없습니다",
)

LEARNING_ENROLLMENT = EntityMeta(
    collection="learning_enrollments",
    prefix="LENR",
    api_path="/api/v1/learning-enrollments",
    tag="학습등록",
    resource="learning_enrollment",
    model=LearningEnrollment,
    create_schema=LearningEnrollmentCreate,
    update_schema=LearningEnrollmentUpdate,
    archetype="transaction",
    not_found_message="학습 등록을 찾을 수 없습니다",
)

LEARNING_CERTIFICATION = EntityMeta(
    collection="learning_certifications",
    prefix="LCRT",
    api_path="/api/v1/learning-certifications",
    tag="학습인증",
    resource="learning_certification",
    model=LearningCertification,
    create_schema=LearningCertificationCreate,
    update_schema=LearningCertificationUpdate,
    archetype="transaction",
    not_found_message="학습 인증을 찾을 수 없습니다",
)

SUCCESSION_PLAN = EntityMeta(
    collection="succession_plans",
    prefix="SUCP",
    api_path="/api/v1/succession-plans",
    tag="승계계획",
    resource="succession_plan",
    model=SuccessionPlan,
    create_schema=SuccessionPlanCreate,
    update_schema=SuccessionPlanUpdate,
    archetype="transaction",
    not_found_message="승계 계획을 찾을 수 없습니다",
)

TALENT_DEVELOPMENT_PLAN = EntityMeta(
    collection="talent_development_plans",
    prefix="TDP",
    api_path="/api/v1/talent-development-plans",
    tag="인재개발계획",
    resource="talent_development_plan",
    model=TalentDevelopmentPlan,
    create_schema=TalentDevelopmentPlanCreate,
    update_schema=TalentDevelopmentPlanUpdate,
    archetype="transaction",
    not_found_message="인재 개발 계획을 찾을 수 없습니다",
)

EMPLOYEE_ENGAGEMENT_SURVEY = EntityMeta(
    collection="employee_engagement_surveys",
    prefix="EESV",
    api_path="/api/v1/employee-engagement-surveys",
    tag="직원참여도설문",
    resource="employee_engagement_survey",
    model=EmployeeEngagementSurvey,
    create_schema=EmployeeEngagementSurveyCreate,
    update_schema=EmployeeEngagementSurveyUpdate,
    archetype="transaction",
    not_found_message="직원 참여도 설문을 찾을 수 없습니다",
)

HEALTH_CHECKUP = EntityMeta(
    collection="health_checkups",
    prefix="HLTH",
    api_path="/api/v1/health-checkups",
    tag="건강검진",
    resource="health_checkup",
    model=HealthCheckup,
    create_schema=HealthCheckupCreate,
    update_schema=HealthCheckupUpdate,
    archetype="transaction",
    not_found_message="건강 검진을 찾을 수 없습니다",
)

SAFETY_TRAINING = EntityMeta(
    collection="safety_trainings",
    prefix="SFTR",
    api_path="/api/v1/safety-trainings",
    tag="안전교육",
    resource="safety_training",
    model=SafetyTraining,
    create_schema=SafetyTrainingCreate,
    update_schema=SafetyTrainingUpdate,
    archetype="transaction",
    not_found_message="안전 교육을 찾을 수 없습니다",
)

SAFETY_INCIDENT = EntityMeta(
    collection="safety_incidents",
    prefix="SFIN",
    api_path="/api/v1/safety-incidents",
    tag="안전사고",
    resource="safety_incident",
    model=SafetyIncident,
    create_schema=SafetyIncidentCreate,
    update_schema=SafetyIncidentUpdate,
    archetype="transaction",
    not_found_message="안전 사고를 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    EMPLOYEE_SKILL_MAP,
    SHIFT_TYPE,
    OVERTIME_POLICY,
    EMPLOYEE_GROUP,
    LEAVE_POLICY,
    LEAVE_PERIOD,
    APPRAISAL_TEMPLATE,
    LEARNING_COURSE,
    COMPETENCY_FRAMEWORK,
    # 트랜잭션
    SHIFT_ASSIGNMENT,
    EMPLOYEE_ONBOARDING,
    EMPLOYEE_OFFBOARDING,
    JOB_OPENING,
    JOB_APPLICANT,
    OFFER_LETTER,
    INTERVIEW_ROUND,
    INTERVIEW_FEEDBACK,
    LEAVE_POLICY_ASSIGNMENT,
    COMPENSATORY_LEAVE_REQUEST,
    SHIFT_REQUEST,
    OVERTIME_ENTRY,
    EMPLOYEE_REFERRAL,
    EMPLOYEE_DOCUMENT_EXPIRY,
    TRAINING_EVENT,
    APPRAISAL_CYCLE,
    APPRAISAL,
    GOAL_SETTING,
    LEARNING_ENROLLMENT,
    LEARNING_CERTIFICATION,
    SUCCESSION_PLAN,
    TALENT_DEVELOPMENT_PLAN,
    EMPLOYEE_ENGAGEMENT_SURVEY,
    HEALTH_CHECKUP,
    SAFETY_TRAINING,
    SAFETY_INCIDENT,
]
