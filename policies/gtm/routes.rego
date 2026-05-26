package gtm.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/gtm/")
    input.user.authenticated == true
    input.user.roles[_] == "gtm_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/gtm/")
    input.user.authenticated == true
    input.user.roles[_] == "gtm_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/gtm/")
    input.user.authenticated == true
    input.user.roles[_] == "gtm_editor"
}
