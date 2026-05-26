package tms.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/tms/")
    input.user.authenticated == true
    input.user.roles[_] == "tms_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/tms/")
    input.user.authenticated == true
    input.user.roles[_] == "tms_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/tms/")
    input.user.authenticated == true
    input.user.roles[_] == "tms_editor"
}
