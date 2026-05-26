# 마이그레이션 규칙(초안)

> FerretDB(Mongo 프로토콜) 환경에서 스키마/인덱스/데이터 보정은 “애플리케이션 레벨 마이그레이션”으로 관리한다.
> Phase 0 이후 실제 실행 도구/형식을 ADR로 확정한다.

## 파일명 규칙

`YYYYMMDD_HHMM__short_description.(py|md)`

예:

- `20260209_1200__init_collections.md`
- `20260210_0930__add_invoice_indexes.py`

## 원칙

- 기본은 forward-only
- 마이그레이션은 멱등성을 고려(재실행 시 안전)
- “인덱스/제약/호환성” 변경은 반드시 ADR 링크 포함

