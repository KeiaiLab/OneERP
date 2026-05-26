"""결재템플릿(ApprovalTemplate) 문서 모델 — 전자결재 모듈."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ApprovalFormField(BaseModel):
    """결재 양식에 표시할 필드 정의."""

    field_key: str
    label: str
    field_type: str = "text"
    required: bool = False
    placeholder: str = ""
    help_text: str = ""


class ApprovalDataBindingField(BaseModel):
    """ERP 문서 값을 결재 양식 필드에 매핑하는 정의."""

    target_field: str
    source_field: str


class ApprovalStepConfig(BaseModel):
    """결재 단계 구성 — 템플릿 내 각 단계의 설정.

    step: 단계 번호 (1부터)
    approver_role: 결재자 역할 (예: "team_lead", "cfo")
    approver: 고정 결재자 ID (역할 대신 지정 시)
    approvers: 합의 결재 시 복수 결재자 목록
    required: 필수 여부
    approval_type: 결재 유형
        - single: 지정 결재자 1명 승인 (기본)
        - consensus: 동일 단계 복수 결재자 전원 승인 필요
    pre_approval_roles: 이 단계에서 전결 가능한 역할 목록
        (해당 역할이 승인하면 이후 단계를 건너뛰고 최종 승인 처리)
    """

    step: int
    approver_role: str = ""
    approver: str = ""
    approvers: list[str] = []
    required: bool = True
    approval_type: str = "single"
    pre_approval_roles: list[str] = []


class ApprovalTemplateCreate(BaseModel):
    """결재템플릿 생성 요청 스키마."""

    template_name: str
    template_code: str = ""
    description: str = ""
    document_type: str = ""
    is_active: bool = True
    steps: list[ApprovalStepConfig] = []
    form_fields: list[ApprovalFormField] = []
    data_binding_fields: list[ApprovalDataBindingField] = []


class ApprovalTemplateUpdate(BaseModel):
    """결재템플릿 수정 요청 스키마."""

    template_name: str | None = None
    template_code: str | None = None
    description: str | None = None
    document_type: str | None = None
    is_active: bool | None = None
    steps: list[ApprovalStepConfig] | None = None
    form_fields: list[ApprovalFormField] | None = None
    data_binding_fields: list[ApprovalDataBindingField] | None = None


class ApprovalTemplate(BaseDocument):
    """결재템플릿 문서 — 전자결재 결재 템플릿 마스터.

    naming prefix: AT
    """

    template_name: str = ""
    template_code: str = ""
    description: str = ""
    document_type: str = ""
    is_active: bool = True
    steps: list[ApprovalStepConfig] = []
    form_fields: list[ApprovalFormField] = []
    data_binding_fields: list[ApprovalDataBindingField] = []


APPROVAL_TEMPLATE_PRESETS: tuple[dict, ...] = (
    {
        "preset_code": "general-proposal",
        "template_name": "품의서 표준",
        "description": "품의/기안 안건을 위한 기본 결재 양식",
        "document_type": "GeneralProposal",
        "steps": [
            {"step": 1, "approver_role": "team_lead", "approval_type": "single"},
            {"step": 2, "approver_role": "department_head", "approval_type": "single"},
        ],
        "form_fields": [
            {
                "field_key": "proposal_title",
                "label": "품의 제목",
                "field_type": "text",
                "required": True,
                "placeholder": "안건 제목을 입력하세요",
            },
            {
                "field_key": "proposal_reason",
                "label": "품의 사유",
                "field_type": "textarea",
                "required": True,
                "help_text": "배경과 기대 효과를 구체적으로 입력합니다.",
            },
            {
                "field_key": "requested_amount",
                "label": "요청 금액",
                "field_type": "currency",
                "required": False,
            },
        ],
        "data_binding_fields": [],
    },
    {
        "preset_code": "expense-claim",
        "template_name": "지출결의서 표준",
        "description": "경비 청구와 증빙 결재를 위한 표준 양식",
        "document_type": "ExpenseClaim",
        "steps": [
            {"step": 1, "approver_role": "team_lead", "approval_type": "single"},
            {"step": 2, "approver_role": "finance_manager", "approval_type": "single"},
        ],
        "form_fields": [
            {
                "field_key": "expense_date",
                "label": "사용 일자",
                "field_type": "date",
                "required": True,
            },
            {
                "field_key": "expense_type",
                "label": "경비 유형",
                "field_type": "select",
                "required": True,
            },
            {
                "field_key": "expense_amount",
                "label": "총 금액",
                "field_type": "currency",
                "required": True,
            },
            {
                "field_key": "receipt_attachment",
                "label": "증빙 첨부",
                "field_type": "attachment",
                "required": False,
            },
        ],
        "data_binding_fields": [
            {"target_field": "신청자", "source_field": "employee"},
            {"target_field": "총금액", "source_field": "total_amount"},
            {"target_field": "경비유형", "source_field": "expense_type"},
        ],
    },
    {
        "preset_code": "purchase-request",
        "template_name": "구매요청 표준",
        "description": "구매 요청 품목과 예산 근거를 결재하는 표준 양식",
        "document_type": "PurchaseRequest",
        "steps": [
            {"step": 1, "approver_role": "team_lead", "approval_type": "single"},
            {"step": 2, "approver_role": "procurement_manager", "approval_type": "single"},
        ],
        "form_fields": [
            {
                "field_key": "request_reason",
                "label": "요청 사유",
                "field_type": "textarea",
                "required": True,
            },
            {
                "field_key": "required_date",
                "label": "필요 일자",
                "field_type": "date",
                "required": True,
            },
            {
                "field_key": "budget_code",
                "label": "예산 코드",
                "field_type": "text",
                "required": False,
            },
        ],
        "data_binding_fields": [
            {"target_field": "요청자", "source_field": "requester_name"},
            {"target_field": "예상금액", "source_field": "estimated_total_amount"},
            {"target_field": "추천공급업체", "source_field": "suggested_supplier_name"},
        ],
    },
)
