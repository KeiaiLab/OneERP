package iot.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/iot/")
    input.user.authenticated == true
    input.user.roles[_] == "iot_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/iot/")
    input.user.authenticated == true
    input.user.roles[_] == "iot_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/iot/")
    input.user.authenticated == true
    input.user.roles[_] == "iot_editor"
}
