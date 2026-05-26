package gateway.routes

import rego.v1

# 기본 거부
default allow := false

# 인증된 사용자는 자기 /me 접근 가능
allow if {
	input.path == "/me"
	input.method == "GET"
	input.user.authenticated == true
}

# admin 역할은 /api/v1/admin/* 접근 가능
allow if {
	startswith(input.path, "/api/v1/admin/")
	input.user.authenticated == true
	"admin" in input.user.roles
}

# manager 는 읽기만 가능 (/api/v1/*/read-only)
allow if {
	startswith(input.path, "/api/v1/")
	input.method == "GET"
	input.user.authenticated == true
	"manager" in input.user.roles
}

# viewer 는 GET / (대시보드) 만
allow if {
	input.path == "/"
	input.method == "GET"
	input.user.authenticated == true
	"viewer" in input.user.roles
}
