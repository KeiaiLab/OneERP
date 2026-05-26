"""PascalCase ↔ snake_case 변환 유틸리티."""

from __future__ import annotations

import re


def pascal_to_snake(name: str) -> str:
    """PascalCase를 snake_case로 변환한다.

    예시:
        >>> pascal_to_snake("GeneralLedgerEntry")
        'general_ledger_entry'
        >>> pascal_to_snake("ETaxInvoice")
        'etax_invoice'
        >>> pascal_to_snake("POSTransaction")
        'pos_transaction'
        >>> pascal_to_snake("KIFRSMapping")
        'kifrs_mapping'
        >>> pascal_to_snake("SLAFulfillment")
        'sla_fulfillment'
        >>> pascal_to_snake("BOMTree")
        'bom_tree'
        >>> pascal_to_snake("OEEMetric")
        'oee_metric'
    """
    # 연속 대문자 뒤에 소문자가 오는 경우 분리 (e.g., "KIFRSMapping" → "KIFRS_Mapping")
    result = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    # 소문자/숫자 뒤에 대문자가 오는 경우 분리 (e.g., "General_Ledger" → 이미 처리됨)
    result = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", result)
    return result.lower()


def snake_to_pascal(name: str) -> str:
    """snake_case를 PascalCase로 변환한다.

    예시:
        >>> snake_to_pascal("general_ledger_entry")
        'GeneralLedgerEntry'
    """
    return "".join(word.capitalize() for word in name.split("_"))
