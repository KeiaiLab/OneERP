package manufacturing.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/manufacturing/")
    input.user.authenticated == true
    input.user.roles[_] == "manufacturing_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/manufacturing/")
    input.user.authenticated == true
    input.user.roles[_] == "manufacturing_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/manufacturing/")
    input.user.authenticated == true
    input.user.roles[_] == "manufacturing_editor"
}
