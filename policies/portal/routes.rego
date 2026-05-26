package portal.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/portal/")
    input.user.authenticated == true
    input.user.roles[_] == "portal_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/portal/")
    input.user.authenticated == true
    input.user.roles[_] == "portal_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/portal/")
    input.user.authenticated == true
    input.user.roles[_] == "portal_editor"
}
