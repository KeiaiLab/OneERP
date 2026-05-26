#!/usr/bin/env bash
# 이벤트 계약 drift 리포트 (Phase 1 스켈레톤).
#
# 목적:
#   - docs/engineering/architecture/event-contracts.md 의 Phase 1 subject 표와
#     코드(core/oneerp_core/events/schemas.py::EventType) 선언을 비교해 단순 리포트를
#     출력한다. 실패로 CI를 차단하지 않는다(리포트 전용 — OPS-04 Phase 1 범위).
#
# 향후 확장:
#   - producer 별 subject 배출 지점(services/*/routes 의 submit_with_event 호출) 수집
#   - consumer 별 구독 subject 수집 후 SoT 표와 양방향 교차 검증
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

SCHEMA="core/oneerp_core/events/schemas.py"
SOT="docs/engineering/architecture/event-contracts.md"

if [[ ! -f "$SCHEMA" ]]; then
  echo "ERROR: schema 파일을 찾을 수 없습니다: $SCHEMA" >&2
  exit 2
fi
if [[ ! -f "$SOT" ]]; then
  echo "ERROR: SoT 문서를 찾을 수 없습니다: $SOT" >&2
  exit 2
fi

echo "== 이벤트 계약 drift 리포트 =="
echo "코드 SoT: $SCHEMA"
echo "문서 SoT: $SOT"
echo

# 코드에서 subject 문자열 추출 (EventType = "..." 형태)
CODE_SUBJECTS=$(grep -oE '"[a-z_]+\.[a-z_]+"' "$SCHEMA" | tr -d '"' | sort -u)
CODE_COUNT=$(printf "%s\n" "$CODE_SUBJECTS" | grep -c . || true)
echo "[코드] EventType 값 개수: ${CODE_COUNT}"

# 문서의 Phase 1 표에 등장한 subject 추출 (oneerp.<something>.<something>)
DOC_SUBJECTS=$(grep -oE 'oneerp\.[a-z_]+\.[a-z_]+' "$SOT" | sed 's/^oneerp\.//' | sort -u)
DOC_COUNT=$(printf "%s\n" "$DOC_SUBJECTS" | grep -c . || true)
echo "[문서] Phase 1 표에 명시된 subject 개수: ${DOC_COUNT}"
echo

# 문서에 명시됐지만 코드에 없는 subject (SoT 문서 오류 후보)
ONLY_DOC=$(comm -23 <(printf "%s\n" "$DOC_SUBJECTS") <(printf "%s\n" "$CODE_SUBJECTS"))
if [[ -n "$ONLY_DOC" ]]; then
  echo "[경고] 문서에는 있으나 코드 EventType에 없는 subject:"
  printf "  - %s\n" $ONLY_DOC
  echo
fi

# 코드에 있으나 Phase 1 표에 명시되지 않은 subject (문서화 미흡 후보)
ONLY_CODE=$(comm -13 <(printf "%s\n" "$DOC_SUBJECTS") <(printf "%s\n" "$CODE_SUBJECTS"))
if [[ -n "$ONLY_CODE" ]]; then
  echo "[정보] 코드에는 있으나 Phase 1 SoT 표에 등재되지 않은 subject:"
  printf "  - %s\n" $ONLY_CODE | head -30
  REST=$(printf "%s\n" $ONLY_CODE | tail -n +31)
  if [[ -n "$REST" ]]; then
    echo "  (… 이하 생략, 전체는 $SCHEMA 참조)"
  fi
  echo
fi

echo "리포트 완료. Phase 1 범위에서는 실패 게이트가 아니며, 후속 phase에서 producer/consumer"
echo "양방향 검사로 확장 예정."
