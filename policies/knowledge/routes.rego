package knowledge.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/knowledge/")
    input.user.authenticated == true
    input.user.roles[_] == "knowledge_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/knowledge/")
    input.user.authenticated == true
    input.user.roles[_] == "knowledge_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/knowledge/")
    input.user.authenticated == true
    input.user.roles[_] == "knowledge_editor"
}
