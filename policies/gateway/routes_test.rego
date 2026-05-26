package gateway.routes_test

import rego.v1
import data.gateway.routes

# 1. 인증 안 된 사용자 거부
test_unauthenticated_denied if {
	not routes.allow with input as {
		"path": "/me",
		"method": "GET",
		"user": {"authenticated": false, "roles": []},
	}
}

# 2. 인증된 사용자 /me 허용
test_authenticated_me_allowed if {
	routes.allow with input as {
		"path": "/me",
		"method": "GET",
		"user": {"authenticated": true, "roles": ["viewer"]},
	}
}

# 3. admin 역할 admin 엔드포인트 허용
test_admin_allowed if {
	routes.allow with input as {
		"path": "/api/v1/admin/tenants",
		"method": "POST",
		"user": {"authenticated": true, "roles": ["admin"]},
	}
}

# 4. viewer 역할 admin 엔드포인트 거부
test_viewer_cannot_admin if {
	not routes.allow with input as {
		"path": "/api/v1/admin/tenants",
		"method": "POST",
		"user": {"authenticated": true, "roles": ["viewer"]},
	}
}

# 5. manager 읽기 허용
test_manager_get_allowed if {
	routes.allow with input as {
		"path": "/api/v1/tenants",
		"method": "GET",
		"user": {"authenticated": true, "roles": ["manager"]},
	}
}

# 6. manager 쓰기 거부
test_manager_post_denied if {
	not routes.allow with input as {
		"path": "/api/v1/tenants",
		"method": "POST",
		"user": {"authenticated": true, "roles": ["manager"]},
	}
}
