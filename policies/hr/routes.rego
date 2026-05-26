package hr.routes

import rego.v1

# 기본 거부
default allow := false

# payroll_admin: /hr/payroll/* 전체 권한 (급여·개인정보)
# 다른 역할은 /hr/payroll/* 을 볼 수 없다
allow if {
	startswith(input.path, "/hr/payroll/")
	input.user.roles[_] == "payroll_admin"
}

# hr_viewer: /hr/* 읽기 허용 (단, /hr/payroll/* 제외)
allow if {
	input.method == "GET"
	startswith(input.path, "/hr/")
	not startswith(input.path, "/hr/payroll/")
	input.user.roles[_] == "hr_viewer"
}

# hr_editor: /hr/employees, /hr/departments, /hr/designations 쓰기 허용
# 단, /hr/payroll/* 은 payroll_admin 만
allow if {
	input.method in {"POST", "PUT", "DELETE"}
	startswith(input.path, "/hr/")
	not startswith(input.path, "/hr/payroll/")
	input.user.roles[_] == "hr_editor"
}

# hr_editor 도 /hr/* 읽기 허용
allow if {
	input.method == "GET"
	startswith(input.path, "/hr/")
	not startswith(input.path, "/hr/payroll/")
	input.user.roles[_] == "hr_editor"
}
