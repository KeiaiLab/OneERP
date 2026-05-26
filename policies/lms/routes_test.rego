package lms.routes_test

import rego.v1
import data.lms.routes

test_viewer_can_get if {
    routes.allow with input as {
        "method": "GET",
        "path": "/lms/records",
        "user": {"authenticated": true, "roles": ["lms_viewer"]},
    }
}

test_anon_denied if {
    not routes.allow with input as {
        "method": "GET",
        "path": "/lms/records",
        "user": {"authenticated": false, "roles": []},
    }
}

test_editor_can_post if {
    routes.allow with input as {
        "method": "POST",
        "path": "/lms/records",
        "user": {"authenticated": true, "roles": ["lms_editor"]},
    }
}

test_viewer_cannot_post if {
    not routes.allow with input as {
        "method": "POST",
        "path": "/lms/records",
        "user": {"authenticated": true, "roles": ["lms_viewer"]},
    }
}

test_cross_module_denied if {
    not routes.allow with input as {
        "method": "GET",
        "path": "/gateway/admin",
        "user": {"authenticated": true, "roles": ["lms_viewer"]},
    }
}

test_unknown_role_denied if {
    not routes.allow with input as {
        "method": "GET",
        "path": "/lms/records",
        "user": {"authenticated": true, "roles": ["guest"]},
    }
}
