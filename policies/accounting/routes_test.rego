package accounting.routes_test

import rego.v1
import data.accounting.routes

# 1. viewer GET 허용
test_viewer_can_get if {
	routes.allow with input as {
		"method": "GET",
		"path": "/accounting/journal",
		"user": {"roles": ["accounting_viewer"]},
	}
}

# 2. 익명(역할 없음) 거부
test_anon_denied if {
	not routes.allow with input as {
		"method": "GET",
		"path": "/accounting/journal",
		"user": {"roles": []},
	}
}

# 3. editor POST 허용
test_editor_can_post if {
	routes.allow with input as {
		"method": "POST",
		"path": "/accounting/journal/new",
		"user": {"roles": ["accounting_editor"]},
	}
}

# 4. viewer POST 거부
test_viewer_cannot_post if {
	not routes.allow with input as {
		"method": "POST",
		"path": "/accounting/journal/new",
		"user": {"roles": ["accounting_viewer"]},
	}
}

# 5. cross-module (hr) 거부
test_cross_module_denied if {
	not routes.allow with input as {
		"method": "GET",
		"path": "/hr/employees",
		"user": {"roles": ["accounting_viewer"]},
	}
}

# 6. unknown role 거부
test_unknown_role_denied if {
	not routes.allow with input as {
		"method": "GET",
		"path": "/accounting/journal",
		"user": {"roles": ["guest"]},
	}
}
