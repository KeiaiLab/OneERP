# LMS 서비스 ERD

> 자동 생성 — 정합성 검증 프로젝트

```mermaid
---
title: LMS 서비스 ERD
---
erDiagram
    LearningCourse {
        string course_name
        string course_code
        string course_type
        string category
        number duration_hours
        number max_enrollment
        boolean is_mandatory
        string status
    }

    LearningEnrollment {
        string employee_id
        string course_id
        date enrollment_date
        date start_date
        date completion_date
        number progress_pct
        number score
        string status
    }

    LearningCertification {
        string employee_id
        string course_id
        string enrollment_id
        string certification_name
        date issued_date
        date expiry_date
        boolean is_mandatory
        string status
    }

    CompetencyFramework {
        string framework_name
        string job_family
        array competencies
        array proficiency_levels
    }

    LearningCourse ||--o{ LearningEnrollment : "course_id"
    LearningEnrollment ||--o| LearningCertification : "enrollment_id"
    LearningCourse ||--o{ LearningCertification : "course_id"
```
