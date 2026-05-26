package pos.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/pos/")
    input.user.authenticated == true
    input.user.roles[_] == "pos_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/pos/")
    input.user.authenticated == true
    input.user.roles[_] == "pos_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/pos/")
    input.user.authenticated == true
    input.user.roles[_] == "pos_editor"
}
