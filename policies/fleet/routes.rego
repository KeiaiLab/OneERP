package fleet.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/fleet/")
    input.user.authenticated == true
    input.user.roles[_] == "fleet_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/fleet/")
    input.user.authenticated == true
    input.user.roles[_] == "fleet_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/fleet/")
    input.user.authenticated == true
    input.user.roles[_] == "fleet_editor"
}
