package marketing_automation.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/marketing-automation/")
    input.user.authenticated == true
    input.user.roles[_] == "marketing-automation_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/marketing-automation/")
    input.user.authenticated == true
    input.user.roles[_] == "marketing-automation_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/marketing-automation/")
    input.user.authenticated == true
    input.user.roles[_] == "marketing-automation_editor"
}
