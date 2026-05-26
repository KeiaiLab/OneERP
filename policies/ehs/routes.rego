package ehs.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/ehs/")
    input.user.authenticated == true
    input.user.roles[_] == "ehs_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/ehs/")
    input.user.authenticated == true
    input.user.roles[_] == "ehs_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/ehs/")
    input.user.authenticated == true
    input.user.roles[_] == "ehs_editor"
}
