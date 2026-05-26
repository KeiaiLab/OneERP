# OneERP HR 서비스 (HR Service)

> 직원, 부서, 채용, 휴가, 근태, 교육, 인사평가 등 인사 관리 전반을 담당하는 서비스 / Manages human resources including employees, departments, recruitment, leave, attendance, training, and appraisals

## 도메인 개요 (Domain Overview)

HR 서비스는 직원 마스터 (Employee Master) 관리, 조직 구조 (Organization Structure) — 부서/직위 (Department/Designation) — 채용 프로세스 (Recruitment Process) — 공고~입사, 휴가/근태 관리 (Leave/Attendance Management), 교대근무 (Shift Management), 초과근무 (Overtime), 인사평가/목표설정 (Appraisal/Goal Setting), 교육훈련 (Training/LMS), 역량관리 (Competency Management), 승계계획 (Succession Planning), 안전관리 (Safety Management) 등 인적자원 관리 전 영역을 담당한다.

## 기술 스택 (Tech Stack)

| 항목 (Item) | 기술 (Technology) |
|-------------|-------------------|
| 프레임워크 (Framework) | FastAPI + Pydantic v2 |
| 데이터베이스 (Database) | FerretDB (MongoDB Protocol) |
| 포트 (Port) | 8006 |

## 엔티티 (Entities) — 43개

### 마스터 데이터 (Master Data)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| Employee | employees | 직원 (Employee) |
| Department | departments | 부서 (Department) |
| Designation | designations | 직위 (Designation) |
| LeaveType | leave_types | 휴가유형 (Leave Type) |
| LeaveBalance | leave_balances | 휴가잔액 (Leave Balance) |
| EmployeeSkillMap | employee_skill_maps | 직원역량맵 (Employee Skill Map) |
| ShiftType | shift_types | 교대유형 (Shift Type) |
| OvertimePolicy | overtime_policies | 초과근무정책 (Overtime Policy) |
| EmployeeGroup | employee_groups | 직원그룹 (Employee Group) |
| LeavePolicy | leave_policies | 휴가정책 (Leave Policy) |
| LeavePeriod | leave_periods | 휴가기간 (Leave Period) |
| AppraisalTemplate | appraisal_templates | 평가템플릿 (Appraisal Template) |
| LearningCourse | learning_courses | 학습과정 (Learning Course) |
| CompetencyFramework | competency_frameworks | 역량프레임워크 (Competency Framework) |

### 트랜잭션 문서 (Transaction Documents)
| 엔티티 (Entity) | 컬렉션 (Collection) | 설명 (Description) |
|-----------------|---------------------|-------------------|
| Attendance | attendances | 출퇴근 (Attendance) |
| EmployeeTransfer | employee_transfers | 인사이동 (Employee Transfer) |
| ShiftAssignment | shift_assignments | 교대배정 (Shift Assignment) |
| EmployeeOnboarding | employee_onboardings | 입사절차 (Employee Onboarding) |
| EmployeeOffboarding | employee_offboardings | 퇴사절차 (Employee Offboarding) |
| JobOpening | job_openings | 채용공고 (Job Opening) |
| JobApplicant | job_applicants | 입사지원자 (Job Applicant) |
| OfferLetter | offer_letters | 채용제안서 (Offer Letter) |
| InterviewRound | interview_rounds | 면접라운드 (Interview Round) |
| InterviewFeedback | interview_feedbacks | 면접피드백 (Interview Feedback) |
| LeavePolicyAssignment | leave_policy_assignments | 휴가정책할당 (Leave Policy Assignment) |
| CompensatoryLeaveRequest | compensatory_leave_requests | 대체휴가신청 (Compensatory Leave Request) |
| ShiftRequest | shift_requests | 교대변경요청 (Shift Change Request) |
| OvertimeEntry | overtime_entries | 초과근무기록 (Overtime Entry) |
| EmployeeReferral | employee_referrals | 직원추천채용 (Employee Referral) |
| EmployeeDocumentExpiry | employee_document_expiries | 직원서류만료 (Employee Document Expiry) |
| TrainingEvent | training_events | 교육이벤트 (Training Event) |
| AppraisalCycle | appraisal_cycles | 평가주기 (Appraisal Cycle) |
| Appraisal | appraisals | 인사평가 (Appraisal) |
| GoalSetting | goal_settings | 목표설정 (Goal Setting) |
| LearningEnrollment | learning_enrollments | 학습등록 (Learning Enrollment) |
| LearningCertification | learning_certifications | 학습인증 (Learning Certification) |
| SuccessionPlan | succession_plans | 승계계획 (Succession Plan) |
| TalentDevelopmentPlan | talent_development_plans | 인재개발계획 (Talent Development Plan) |
| EmployeeEngagementSurvey | employee_engagement_surveys | 직원참여도설문 (Employee Engagement Survey) |
| HealthCheckup | health_checkups | 건강검진 (Health Checkup) |
| SafetyTraining | safety_trainings | 안전교육 (Safety Training) |
| SafetyIncident | safety_incidents | 안전사고 (Safety Incident) |

## 비즈니스 로직 (Business Logic)

| 서비스 (Service) | 주요 메서드 (Key Methods) | 설명 (Description) |
|-----------------|-------------------------|-------------------|
| LeaveService | 휴가 신청, 승인/반려, 잔액 계산 | 휴가 워크플로우 관리 (Leave Workflow) |
| OnboardingService | 입사 체크리스트 관리 | 입사 프로세스 자동화 (Onboarding Automation) |
| RecruitmentService | 채용 파이프라인 관리 | 공고~입사 전체 흐름 (Recruitment Pipeline) |
| ShiftService | 교대 스케줄 생성/배정 | 교대근무 관리 (Shift Management) |
| SkillMapService | 역량 매핑, 갭 분석 | 직원 역량 관리 (Skill Map Management) |
| TransferService | 인사이동 처리 | 부서/직위 변경 (Employee Transfer) |

## API 엔드포인트 (API Endpoints)

### 자동 생성 CRUD (Auto-generated CRUD)
EntityMeta 기반 42개 엔드포인트 자동 생성 (Auto-generated from EntityMeta)

### 커스텀 라우트 (Custom Routes)
| 메서드 (Method) | 경로 (Path) | 설명 (Description) |
|----------------|-------------|-------------------|
| CRUD | /api/v1/leave-applications | 휴가 신청 (Leave Applications) — 승인/반려 포함 |

## 실행 방법 (How to Run)

```bash
uv run --package oneerp-hr --directory services/hr uvicorn app.main:app --port 8006
```

## 테스트 (Testing)

```bash
uv run pytest services/hr/ -m "not integration and not e2e" -v
```
