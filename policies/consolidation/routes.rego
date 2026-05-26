package consolidation.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/consolidation/")
    input.user.authenticated == true
    input.user.roles[_] == "consolidation_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/consolidation/")
    input.user.authenticated == true
    input.user.roles[_] == "consolidation_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/consolidation/")
    input.user.authenticated == true
    input.user.roles[_] == "consolidation_editor"
}
