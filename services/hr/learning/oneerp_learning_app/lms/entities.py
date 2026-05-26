"""LMS 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

4개 엔티티를 EntityMeta로 선언한다.
LearningCourse(마스터), CompetencyFramework(마스터),
LearningEnrollment(트랜잭션), LearningCertification(트랜잭션).
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.competency_framework import (
    CompetencyFramework,
    CompetencyFrameworkCreate,
    CompetencyFrameworkUpdate,
)
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

LEARNING_COURSE = EntityMeta(
    collection="learning_courses",
    prefix="LC",
    api_path="/api/v1/learning-courses",
    tag="교육 과정",
    resource="learning_course",
    model=LearningCourse,
    create_schema=LearningCourseCreate,
    update_schema=LearningCourseUpdate,
    archetype="master",
    not_found_message="교육 과정을 찾을 수 없습니다",
)

COMPETENCY_FRAMEWORK = EntityMeta(
    collection="competency_frameworks",
    prefix="CF",
    api_path="/api/v1/competency-frameworks",
    tag="역량 체계",
    resource="competency_framework",
    model=CompetencyFramework,
    create_schema=CompetencyFrameworkCreate,
    update_schema=CompetencyFrameworkUpdate,
    archetype="master",
    not_found_message="역량 체계를 찾을 수 없습니다",
)

LEARNING_ENROLLMENT = EntityMeta(
    collection="learning_enrollments",
    prefix="LE",
    api_path="/api/v1/learning-enrollments",
    tag="수강 등록",
    resource="learning_enrollment",
    model=LearningEnrollment,
    create_schema=LearningEnrollmentCreate,
    update_schema=LearningEnrollmentUpdate,
    archetype="transaction",
    not_found_message="수강 등록을 찾을 수 없습니다",
)

LEARNING_CERTIFICATION = EntityMeta(
    collection="learning_certifications",
    prefix="LCRT",
    api_path="/api/v1/learning-certifications",
    tag="교육 인증",
    resource="learning_certification",
    model=LearningCertification,
    create_schema=LearningCertificationCreate,
    update_schema=LearningCertificationUpdate,
    archetype="transaction",
    not_found_message="교육 인증을 찾을 수 없습니다",
)

ENTITY_METAS = [
    LEARNING_COURSE,
    COMPETENCY_FRAMEWORK,
    LEARNING_ENROLLMENT,
    LEARNING_CERTIFICATION,
]
