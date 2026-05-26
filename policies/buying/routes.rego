package buying.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/buying/")
    input.user.authenticated == true
    input.user.roles[_] == "buying_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/buying/")
    input.user.authenticated == true
    input.user.roles[_] == "buying_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/buying/")
    input.user.authenticated == true
    input.user.roles[_] == "buying_editor"
}
