package directory.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/directory/")
    input.user.authenticated == true
    input.user.roles[_] == "directory_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/directory/")
    input.user.authenticated == true
    input.user.roles[_] == "directory_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/directory/")
    input.user.authenticated == true
    input.user.roles[_] == "directory_editor"
}
