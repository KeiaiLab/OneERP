package plm.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/plm/")
    input.user.authenticated == true
    input.user.roles[_] == "plm_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/plm/")
    input.user.authenticated == true
    input.user.roles[_] == "plm_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/plm/")
    input.user.authenticated == true
    input.user.roles[_] == "plm_editor"
}
