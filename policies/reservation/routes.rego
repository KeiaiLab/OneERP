package reservation.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/reservation/")
    input.user.authenticated == true
    input.user.roles[_] == "reservation_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/reservation/")
    input.user.authenticated == true
    input.user.roles[_] == "reservation_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/reservation/")
    input.user.authenticated == true
    input.user.roles[_] == "reservation_editor"
}
