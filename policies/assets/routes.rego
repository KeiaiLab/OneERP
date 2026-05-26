package assets.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/assets/")
    input.user.authenticated == true
    input.user.roles[_] == "assets_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/assets/")
    input.user.authenticated == true
    input.user.roles[_] == "assets_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/assets/")
    input.user.authenticated == true
    input.user.roles[_] == "assets_editor"
}
