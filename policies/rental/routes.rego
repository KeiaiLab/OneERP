package rental.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/rental/")
    input.user.authenticated == true
    input.user.roles[_] == "rental_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/rental/")
    input.user.authenticated == true
    input.user.roles[_] == "rental_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/rental/")
    input.user.authenticated == true
    input.user.roles[_] == "rental_editor"
}
