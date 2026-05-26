package ecommerce.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/ecommerce/")
    input.user.authenticated == true
    input.user.roles[_] == "ecommerce_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/ecommerce/")
    input.user.authenticated == true
    input.user.roles[_] == "ecommerce_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/ecommerce/")
    input.user.authenticated == true
    input.user.roles[_] == "ecommerce_editor"
}
