package board.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/board/")
    input.user.authenticated == true
    input.user.roles[_] == "board_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/board/")
    input.user.authenticated == true
    input.user.roles[_] == "board_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/board/")
    input.user.authenticated == true
    input.user.roles[_] == "board_editor"
}
