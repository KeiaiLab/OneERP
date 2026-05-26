package integration_hub.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/integration-hub/")
    input.user.authenticated == true
    input.user.roles[_] == "integration-hub_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/integration-hub/")
    input.user.authenticated == true
    input.user.roles[_] == "integration-hub_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/integration-hub/")
    input.user.authenticated == true
    input.user.roles[_] == "integration-hub_editor"
}
