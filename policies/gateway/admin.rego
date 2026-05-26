package gateway.admin

import rego.v1

# admin 역할의 tenant 관리
default tenant_mutation := false

tenant_mutation if {
	input.method in {"POST", "PUT", "DELETE"}
	startswith(input.path, "/api/v1/admin/tenants")
	"admin" in input.user.roles
	input.user.authenticated == true
}
