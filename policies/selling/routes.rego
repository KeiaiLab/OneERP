package selling.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/selling/")
    input.user.authenticated == true
    input.user.roles[_] == "selling_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/selling/")
    input.user.authenticated == true
    input.user.roles[_] == "selling_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/selling/")
    input.user.authenticated == true
    input.user.roles[_] == "selling_editor"
}
