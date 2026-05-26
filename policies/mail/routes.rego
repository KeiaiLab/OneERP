package mail.routes

import rego.v1

default allow := false

allow if {
    input.method == "GET"
    startswith(input.path, "/mail/")
    input.user.authenticated == true
    input.user.roles[_] == "mail_viewer"
}

allow if {
    input.method in {"POST", "PUT", "DELETE"}
    startswith(input.path, "/mail/")
    input.user.authenticated == true
    input.user.roles[_] == "mail_editor"
}

allow if {
    input.method == "GET"
    startswith(input.path, "/mail/")
    input.user.authenticated == true
    input.user.roles[_] == "mail_editor"
}
