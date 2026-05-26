package expenses.routes_test

import rego.v1
import data.expenses.routes

test_viewer_can_get if {
    routes.allow with input as {
        "method": "GET",
        "path": "/expenses/records",
        "user": {"authenticated": true, "roles": ["expenses_viewer"]},
    }
}

test_anon_denied if {
    not routes.allow with input as {
        "method": "GET",
        "path": "/expenses/records",
        "user": {"authenticated": false, "roles": []},
    }
}

test_editor_can_post if {
    routes.allow with input as {
        "method": "POST",
        "path": "/expenses/records",
        "user": {"authenticated": true, "roles": ["expenses_editor"]},
    }
}

test_viewer_cannot_post if {
    not routes.allow with input as {
        "method": "POST",
        "path": "/expenses/records",
        "user": {"authenticated": true, "roles": ["expenses_viewer"]},
    }
}

test_cross_module_denied if {
    not routes.allow with input as {
        "method": "GET",
        "path": "/gateway/admin",
        "user": {"authenticated": true, "roles": ["expenses_viewer"]},
    }
}

test_unknown_role_denied if {
    not routes.allow with input as {
        "method": "GET",
        "path": "/expenses/records",
        "user": {"authenticated": true, "roles": ["guest"]},
    }
}
