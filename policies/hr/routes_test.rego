package hr.routes_test

import rego.v1
import data.hr.routes

# 1. hr_viewer GET /hr/employees 허용
test_viewer_can_get_employees if {
	routes.allow with input as {
		"method": "GET",
		"path": "/hr/employees",
		"user": {"roles": ["hr_viewer"]},
	}
}

# 2. hr_editor POST /hr/employees 허용
test_editor_can_post_employees if {
	routes.allow with input as {
		"method": "POST",
		"path": "/hr/employees",
		"user": {"roles": ["hr_editor"]},
	}
}

# 3. payroll_admin GET /hr/payroll/salary 허용
test_payroll_admin_can_get_payroll if {
	routes.allow with input as {
		"method": "GET",
		"path": "/hr/payroll/salary",
		"user": {"roles": ["payroll_admin"]},
	}
}

# 4. hr_viewer /hr/payroll/* 거부 (개인정보 보호)
test_viewer_denied_payroll if {
	not routes.allow with input as {
		"method": "GET",
		"path": "/hr/payroll/salary",
		"user": {"roles": ["hr_viewer"]},
	}
}

# 5. hr_editor /hr/payroll/* 거부 (payroll_admin 만 허용)
test_editor_denied_payroll if {
	not routes.allow with input as {
		"method": "POST",
		"path": "/hr/payroll/salary",
		"user": {"roles": ["hr_editor"]},
	}
}

# 6. hr_viewer POST 거부 (쓰기 권한 없음)
test_viewer_cannot_post if {
	not routes.allow with input as {
		"method": "POST",
		"path": "/hr/employees",
		"user": {"roles": ["hr_viewer"]},
	}
}

# 7. cross-module (accounting) 거부
test_cross_module_denied if {
	not routes.allow with input as {
		"method": "GET",
		"path": "/accounting/journal",
		"user": {"roles": ["hr_viewer"]},
	}
}

# 8. 익명 거부
test_anon_denied if {
	not routes.allow with input as {
		"method": "GET",
		"path": "/hr/employees",
		"user": {"roles": []},
	}
}

# 9. unknown role 거부
test_unknown_role_denied if {
	not routes.allow with input as {
		"method": "GET",
		"path": "/hr/payroll/salary",
		"user": {"roles": ["guest"]},
	}
}
