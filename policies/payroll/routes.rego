package payroll.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/payroll/")
    input.user.authenticated == true
    input.user.roles[_] == "payroll_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/payroll/")
    input.user.authenticated == true
    input.user.roles[_] == "payroll_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/payroll/")
    input.user.authenticated == true
    input.user.roles[_] == "payroll_editor"
}
