package lms.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/lms/")
    input.user.authenticated == true
    input.user.roles[_] == "lms_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/lms/")
    input.user.authenticated == true
    input.user.roles[_] == "lms_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/lms/")
    input.user.authenticated == true
    input.user.roles[_] == "lms_editor"
}
