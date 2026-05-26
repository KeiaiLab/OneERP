package analytics.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/analytics/")
    input.user.authenticated == true
    input.user.roles[_] == "analytics_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/analytics/")
    input.user.authenticated == true
    input.user.roles[_] == "analytics_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/analytics/")
    input.user.authenticated == true
    input.user.roles[_] == "analytics_editor"
}
