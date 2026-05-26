package survey.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/survey/")
    input.user.authenticated == true
    input.user.roles[_] == "survey_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/survey/")
    input.user.authenticated == true
    input.user.roles[_] == "survey_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/survey/")
    input.user.authenticated == true
    input.user.roles[_] == "survey_editor"
}
