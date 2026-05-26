package documents.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/documents/")
    input.user.authenticated == true
    input.user.roles[_] == "documents_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/documents/")
    input.user.authenticated == true
    input.user.roles[_] == "documents_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/documents/")
    input.user.authenticated == true
    input.user.roles[_] == "documents_editor"
}
