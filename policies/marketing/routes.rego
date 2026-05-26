package marketing.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/marketing/")
    input.user.authenticated == true
    input.user.roles[_] == "marketing_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/marketing/")
    input.user.authenticated == true
    input.user.roles[_] == "marketing_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/marketing/")
    input.user.authenticated == true
    input.user.roles[_] == "marketing_editor"
}
