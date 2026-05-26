package stock.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/stock/")
    input.user.authenticated == true
    input.user.roles[_] == "stock_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/stock/")
    input.user.authenticated == true
    input.user.roles[_] == "stock_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/stock/")
    input.user.authenticated == true
    input.user.roles[_] == "stock_editor"
}
