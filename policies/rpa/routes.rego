package rpa.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/rpa/")
    input.user.authenticated == true
    input.user.roles[_] == "rpa_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/rpa/")
    input.user.authenticated == true
    input.user.roles[_] == "rpa_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/rpa/")
    input.user.authenticated == true
    input.user.roles[_] == "rpa_editor"
}
