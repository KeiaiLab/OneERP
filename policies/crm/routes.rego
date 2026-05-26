package crm.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/crm/")
    input.user.authenticated == true
    input.user.roles[_] == "crm_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/crm/")
    input.user.authenticated == true
    input.user.roles[_] == "crm_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/crm/")
    input.user.authenticated == true
    input.user.roles[_] == "crm_editor"
}
