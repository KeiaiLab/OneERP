package messenger.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/messenger/")
    input.user.authenticated == true
    input.user.roles[_] == "messenger_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/messenger/")
    input.user.authenticated == true
    input.user.roles[_] == "messenger_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/messenger/")
    input.user.authenticated == true
    input.user.roles[_] == "messenger_editor"
}
