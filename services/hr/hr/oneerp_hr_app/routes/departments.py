"""부서(Department) 커스텀 라우터.

조직도 트리 조회와 조직 구조 무결성 검증을 함께 제공한다.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_hr_app.models.department import Department, DepartmentCreate, DepartmentUpdate

router = APIRouter(prefix="/api/v1/departments", tags=["부서"])

_COLLECTION = "departments"
_EMPLOYEE_COLLECTION = "employees"
_PREFIX = "DEPT"
_NOT_FOUND_MESSAGE = "부서를 찾을 수 없습니다"


def _get_department_repo(tenant_id: str) -> Repository:
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_employee_repo(tenant_id: str) -> Repository:
    return Repository(_EMPLOYEE_COLLECTION, tenant_id=tenant_id)


def _with_public_id(document: dict[str, Any]) -> dict[str, Any]:
    public = dict(document)
    if "_id" in public:
        public["id"] = public["_id"]
    return public


def _normalize_parent_department(parent_department: str | None) -> str | None:
    if not parent_department:
        return None
    return parent_department


def _is_descendant(
    documents: list[dict[str, Any]],
    *,
    root_id: str,
    candidate_parent_id: str,
) -> bool:
    children_by_parent: dict[str | None, list[str]] = defaultdict(list)
    for document in documents:
        children_by_parent[document.get("parent_department")].append(document["_id"])

    stack = list(children_by_parent.get(root_id, []))
    descendants: set[str] = set()
    while stack:
        child_id = stack.pop()
        if child_id in descendants:
            continue
        descendants.add(child_id)
        stack.extend(children_by_parent.get(child_id, []))
    return candidate_parent_id in descendants


def _validate_parent_department(
    repo: Repository,
    *,
    parent_department: str | None,
    current_department_id: str | None = None,
) -> None:
    parent_department = _normalize_parent_department(parent_department)
    if not parent_department:
        return

    parent = repo.find_by_id(parent_department)
    if not parent:
        raise_unprocessable("ERR-HR-044", "상위 부서를 찾을 수 없습니다")

    if current_department_id and parent_department == current_department_id:
        raise_unprocessable(
            "ERR-HR-045", "자기 자신 또는 하위 부서를 상위 부서로 지정할 수 없습니다"
        )

    if current_department_id:
        documents = repo.find_many(limit=1000, sort=[("department_name", 1)])
        if _is_descendant(
            documents,
            root_id=current_department_id,
            candidate_parent_id=parent_department,
        ):
            raise_unprocessable(
                "ERR-HR-045", "자기 자신 또는 하위 부서를 상위 부서로 지정할 수 없습니다"
            )


@router.post("", status_code=201, dependencies=[Depends(require_permission("department:create"))])
def create_department(body: DepartmentCreate, user: CurrentUserDep) -> dict[str, Any]:
    """부서를 생성한다."""
    repo = _get_department_repo(user.tenant_id)
    payload = body.model_dump()
    payload["parent_department"] = _normalize_parent_department(payload.get("parent_department"))
    _validate_parent_department(repo, parent_department=payload.get("parent_department"))

    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    department = Department(
        _id=doc_id,
        tenant_id=user.tenant_id,
        created_by=user.sub,
        updated_by=user.sub,
        **payload,
    )
    repo.insert(department)
    return {"_id": doc_id, "id": doc_id, **payload}


@router.get("", dependencies=[Depends(require_permission("department:read"))])
def list_departments(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """부서 목록을 페이지네이션으로 조회한다."""
    repo = _get_department_repo(user.tenant_id)
    skip = (page - 1) * page_size
    docs = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    return {
        "data": [_with_public_id(doc) for doc in docs],
        "total": repo.count(),
        "page": page,
        "page_size": page_size,
    }


@router.get("/tree", dependencies=[Depends(require_permission("department:read"))])
def get_department_tree(user: CurrentUserDep) -> dict[str, Any]:
    """조직도 트리를 조회한다."""
    department_repo = _get_department_repo(user.tenant_id)
    employee_repo = _get_employee_repo(user.tenant_id)
    departments = department_repo.find_many(limit=1000, sort=[("department_name", 1)])
    employees = employee_repo.find_many(limit=10000, sort=[("department", 1)])
    employee_counts = Counter(
        employee.get("department", "")
        for employee in employees
        if employee.get("department") and str(employee.get("status", "active")).lower() != "left"
    )

    nodes: dict[str, dict[str, Any]] = {}
    roots: list[dict[str, Any]] = []

    for department in departments:
        node = _with_public_id(department)
        node["children"] = []
        node["employee_count"] = employee_counts.get(node.get("department_name", ""), 0)
        node["child_count"] = 0
        nodes[node["_id"]] = node

    for node in nodes.values():
        parent_id = node.get("parent_department")
        parent = nodes.get(str(parent_id)) if parent_id is not None else None
        if parent is None:
            roots.append(node)
            continue
        parent["children"].append(node)

    for node in nodes.values():
        node["children"].sort(key=lambda child: child.get("department_name", ""))
        node["child_count"] = len(node["children"])
    roots.sort(key=lambda node: node.get("department_name", ""))

    return {"data": roots, "total": len(departments)}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("department:read"))])
def get_department(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """부서 상세를 조회한다."""
    repo = _get_department_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert doc is not None
    return _with_public_id(doc)


@router.put("/{doc_id}", dependencies=[Depends(require_permission("department:write"))])
def update_department(
    doc_id: str,
    body: DepartmentUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """부서를 수정한다."""
    repo = _get_department_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert doc is not None
    update_data = body.model_dump(exclude_none=True)
    if "parent_department" in update_data:
        update_data["parent_department"] = _normalize_parent_department(
            update_data.get("parent_department")
        )
        _validate_parent_department(
            repo,
            parent_department=update_data.get("parent_department"),
            current_department_id=doc_id,
        )
    update_data["updated_by"] = user.sub
    repo.update_by_id(doc_id, update_data)
    return _with_public_id({**doc, **update_data})


@router.delete(
    "/{doc_id}", status_code=204, dependencies=[Depends(require_permission("department:delete"))]
)
def delete_department(doc_id: str, user: CurrentUserDep) -> None:
    """하위 부서와 재직 중 직원이 없을 때만 부서를 삭제한다."""
    repo = _get_department_repo(user.tenant_id)
    employee_repo = _get_employee_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert doc is not None
    if repo.count({"parent_department": doc_id}) > 0:
        raise_unprocessable("ERR-HR-033", "하위 부서가 있어 삭제할 수 없습니다")
    if employee_repo.count({"department": doc.get("department_name", "")}) > 0:
        raise_unprocessable("ERR-HR-046", "직원이 배정된 부서는 삭제할 수 없습니다")
    repo.delete_by_id(doc_id)
