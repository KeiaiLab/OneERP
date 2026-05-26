# items — 2026-04-13 (본게임 Phase 6 전파)

customers/suppliers 패턴 3번째 전파. mock-gateway 헬퍼 0 변경.

## 결과

| 영역 | 결과 |
|------|------|
| list 4 상태 + baseline | 4 PASS + baseline 1 |
| detail 5 시나리오 | 5 PASS + baseline 1 |
| form 4 시나리오 | 4 PASS + baseline 1 |
| responsive sm/md/lg | 3 PASS + baseline 3 |
| **a11y 3 페이지** | **3 PASS — 위반 0** |

**누적 57 PASS** (customers 19 + suppliers 19 + items 19, 9.5s)

## a11y 핵심 — Select 수정의 진짜 검증

items 폼은 `valuation_method`(select 타입) 필드를 가진다. Phase 4의 `field-renderer.tsx` 수정(`SelectTrigger` 에 `aria-label={field.label}`)이 customers/suppliers 에는 select 필드가 없어 우회된 셈이었지만, items 에서 비로소 **실제 select 트리거를 가진 페이지의 a11y 통과**로 검증됨.

→ Phase 4 의 button-name 위반 해소 패치가 수정 의도대로 동작함을 다른 엔티티에서 확정.

## 증거 (6 baseline)

- `before-list-normal.png` / `before-detail-normal.png` / `before-form-blank.png`
- `before-list-sm.png` / `before-list-md.png` / `before-list-lg.png`

## 디스커버리

- 첫 검증 메시지가 "품목코드은(는) 필수입니다" — required 3 필드 중 첫 번째(item_code)만 메시지로 노출. react-hook-form 이 첫 에러만 표시하는 동작.
- checkbox 필드(is_stock_item, has_batch_no, has_serial_no) 는 본 Phase 에서 별도 시나리오 없음 — 향후 횡단 필요 시 추가.
