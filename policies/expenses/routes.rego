package expenses.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/expenses/")
    input.user.authenticated == true
    input.user.roles[_] == "expenses_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/expenses/")
    input.user.authenticated == true
    input.user.roles[_] == "expenses_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/expenses/")
    input.user.authenticated == true
    input.user.roles[_] == "expenses_editor"
}
