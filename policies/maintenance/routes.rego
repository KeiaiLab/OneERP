package maintenance.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/maintenance/")
    input.user.authenticated == true
    input.user.roles[_] == "maintenance_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/maintenance/")
    input.user.authenticated == true
    input.user.roles[_] == "maintenance_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/maintenance/")
    input.user.authenticated == true
    input.user.roles[_] == "maintenance_editor"
}
