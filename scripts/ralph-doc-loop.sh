#!/usr/bin/env bash
# ralph-doc-loop.sh — OneERP 모듈 문서 생산 Ralph Loop
#
# 사용법:
#   bash scripts/ralph-doc-loop.sh              # 포그라운드 실행
#   nohup bash scripts/ralph-doc-loop.sh &      # 백그라운드 실행
#   tmux new -d -s ralph 'bash scripts/ralph-doc-loop.sh'  # tmux 실행
#
# 중지:
#   touch /tmp/ralph-doc-stop                   # 안전한 중지 (현재 모듈 완료 후)
#   kill $(cat ralph-loop.pid)                  # 즉시 중지

set -uo pipefail
# set -e 제거: claude 비정상 종료 시에도 루프 계속 진행

# ─── 설정 ───────────────────────────────────────
PROJECT_DIR="/Users/phil/WorkSpace/apps/OneErp"
PROMPT_FILE="$PROJECT_DIR/docs/product/scope/RALPH-PROMPT.md"
LOG_DIR="$PROJECT_DIR/.remember/logs/ralph-docs"
MAX_ITERATIONS=9999
STOP_FILE="/tmp/ralph-doc-stop"
# ────────────────────────────────────────────────

mkdir -p "$LOG_DIR"
rm -f "$STOP_FILE"
echo $$ > "$PROJECT_DIR/ralph-loop.pid"

ITERATION=0
START_TIME=$(date +%s)

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_DIR/ralph-loop.log"
}

log "=== Ralph Doc Loop 시작 ==="
log "프로젝트: $PROJECT_DIR"
log "최대 이터레이션: $MAX_ITERATIONS"
log "PID: $$"
log "중지하려면: touch $STOP_FILE"

while [ $ITERATION -lt $MAX_ITERATIONS ]; do
  # 안전한 중지 체크
  if [ -f "$STOP_FILE" ]; then
    log "중지 파일 감지. 루프를 종료합니다."
    rm -f "$STOP_FILE"
    break
  fi

  ITERATION=$((ITERATION + 1))
  ITER_START=$(date +%s)
  ITER_LOG="$LOG_DIR/iteration-$(printf '%03d' $ITERATION).log"

  log "─── 이터레이션 $ITERATION/$MAX_ITERATIONS 시작 ───"

  # Claude Code CLI 실행
  # -p: 비대화형 모드 (print & exit)
  # --dangerously-skip-permissions: 권한 확인 생략
  # cd로 프로젝트 디렉토리 이동 후 실행 (CLAUDE.md 자동 로드)
  cd "$PROJECT_DIR"
  cat "$PROMPT_FILE" | claude -p \
    --dangerously-skip-permissions \
    --model opus \
    --verbose \
    2>&1 | tee "$ITER_LOG" || true

  ITER_END=$(date +%s)
  ITER_DURATION=$(( ITER_END - ITER_START ))

  log "이터레이션 $ITERATION 완료 (${ITER_DURATION}초)"

  # 완료 신호 체크
  if grep -q "ALL 56 MODULES COMPLETE" "$ITER_LOG" 2>/dev/null; then
    log "=== 전체 56개 모듈 완료! ==="
    break
  fi

  # 이터레이션 간 쿨다운 (API 레이트 리밋 방지)
  log "다음 이터레이션까지 10초 대기..."
  sleep 10
done

END_TIME=$(date +%s)
TOTAL_DURATION=$(( END_TIME - START_TIME ))
HOURS=$(( TOTAL_DURATION / 3600 ))
MINUTES=$(( (TOTAL_DURATION % 3600) / 60 ))

log "=== Ralph Doc Loop 종료 ==="
log "총 이터레이션: $ITERATION"
log "총 소요 시간: ${HOURS}시간 ${MINUTES}분"
log "생성된 문서 수: $(find "$PROJECT_DIR/docs/product/scope/modules" -name 'L*.md' 2>/dev/null | wc -l | tr -d ' ')"

rm -f "$PROJECT_DIR/ralph-loop.pid"
