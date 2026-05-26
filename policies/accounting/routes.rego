package accounting.routes

import rego.v1

# 기본 거부
default allow := false

# accounting_viewer: /accounting/* 읽기 허용
allow if {
	input.method == "GET"
	startswith(input.path, "/accounting/")
	input.user.roles[_] == "accounting_viewer"
}

# accounting_editor: /accounting/journal 쓰기 허용
allow if {
	input.method in {"POST", "PUT", "DELETE"}
	startswith(input.path, "/accounting/journal")
	input.user.roles[_] == "accounting_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/accounting/")
    input.user.roles[_] == "accounting_editor"
}
