package esg.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/esg/")
    input.user.authenticated == true
    input.user.roles[_] == "esg_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/esg/")
    input.user.authenticated == true
    input.user.roles[_] == "esg_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/esg/")
    input.user.authenticated == true
    input.user.roles[_] == "esg_editor"
}
