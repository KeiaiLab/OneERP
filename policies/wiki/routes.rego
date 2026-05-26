package wiki.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/wiki/")
    input.user.authenticated == true
    input.user.roles[_] == "wiki_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/wiki/")
    input.user.authenticated == true
    input.user.roles[_] == "wiki_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/wiki/")
    input.user.authenticated == true
    input.user.roles[_] == "wiki_editor"
}
