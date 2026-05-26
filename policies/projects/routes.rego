package projects.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/projects/")
    input.user.authenticated == true
    input.user.roles[_] == "projects_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/projects/")
    input.user.authenticated == true
    input.user.roles[_] == "projects_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/projects/")
    input.user.authenticated == true
    input.user.roles[_] == "projects_editor"
}
