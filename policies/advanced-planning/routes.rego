package advanced_planning.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/advanced-planning/")
    input.user.authenticated == true
    input.user.roles[_] == "advanced-planning_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/advanced-planning/")
    input.user.authenticated == true
    input.user.roles[_] == "advanced-planning_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/advanced-planning/")
    input.user.authenticated == true
    input.user.roles[_] == "advanced-planning_editor"
}
