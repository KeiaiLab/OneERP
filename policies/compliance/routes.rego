package compliance.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/compliance/")
    input.user.authenticated == true
    input.user.roles[_] == "compliance_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/compliance/")
    input.user.authenticated == true
    input.user.roles[_] == "compliance_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/compliance/")
    input.user.authenticated == true
    input.user.roles[_] == "compliance_editor"
}
