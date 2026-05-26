package subscriptions.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/subscriptions/")
    input.user.authenticated == true
    input.user.roles[_] == "subscriptions_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/subscriptions/")
    input.user.authenticated == true
    input.user.roles[_] == "subscriptions_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/subscriptions/")
    input.user.authenticated == true
    input.user.roles[_] == "subscriptions_editor"
}
