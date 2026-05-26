package quality.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/quality/")
    input.user.authenticated == true
    input.user.roles[_] == "quality_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/quality/")
    input.user.authenticated == true
    input.user.roles[_] == "quality_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/quality/")
    input.user.authenticated == true
    input.user.roles[_] == "quality_editor"
}
