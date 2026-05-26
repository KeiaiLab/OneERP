package clm.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/clm/")
    input.user.authenticated == true
    input.user.roles[_] == "clm_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/clm/")
    input.user.authenticated == true
    input.user.roles[_] == "clm_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/clm/")
    input.user.authenticated == true
    input.user.roles[_] == "clm_editor"
}
