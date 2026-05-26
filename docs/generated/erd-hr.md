# HR 서비스 ERD

> 자동 생성 — `scripts/docs/gen_erd.py`

```mermaid
---
title: HR 서비스 ERD
---
erDiagram
    Attendance {
        string employee_id
        string employee_name
        date attendance_date
        string status
    }
    Department {
        string department_name
        string parent_department
        boolean is_group
        string company
    }
    Designation {
        string title
        string description
    }
    Employee {
        string employee_name
        string department
        string designation
        date date_of_joining
        string status
        string gender
        string email
        string phone
        string company
    }
    EmployeeOffboarding {
        string employee
        date offboarding_date
        string activities
    }
    EmployeeOnboarding {
        string employee
        date onboarding_date
        string activities
    }
    EmployeeSkillMap {
        string employee
        string skills
    }
    EmployeeTransfer {
        string employee
        string employee_name
        date transfer_date
        string from_department
        string to_department
        string from_designation
        string to_designation
        string reason
    }
    LeaveApplication {
        string employee_id
        string employee_name
        string leave_type
        date from_date
        date to_date
        number total_days
        string status
        string reason
    }
    LeaveBalance {
        string employee
        string leave_type
        number total_allocated
        number total_used
        number balance
    }
    LeaveType {
        string leave_type_name
        number max_leaves_allowed
        boolean is_carry_forward
        boolean is_paid
    }
    ShiftAssignment {
        string employee
        string shift_type
        date start_date
        date end_date
    }
```
