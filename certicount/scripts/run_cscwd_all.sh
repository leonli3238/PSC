#!/usr/bin/env bash
# Unattended driver for the remaining CSCWD stages (方案 B).
#
# It re-implements nothing: every experiment command is one stage of scripts/run_cscwd.sh,
# executed in the order documented in that file's header. This script only adds
#   - a clean-tree precondition (no "-dirty" revision in results/logs/cscwd_commands.log),
#   - one log per stage (/tmp/<stage>.log, truncated at start),
#   - fail-fast on non-zero exit and on fatal patterns,
#   - a gate before cs1-audit so the planned call volume can be reported first,
#   - a driver log (/tmp/cscwd_all.log) with start/end and per-stage wall time.
#
# Usage (from certicount/ or anywhere):
#   nohup bash scripts/run_cscwd_all.sh > /dev/null 2>&1 &
#
# Environment:
#   STAGES  stage list, default "cs1-small cs1-decomp cs1-audit-dry cs1-audit cs2 cs0-alpha cs3 cs3-code cs3b"
#   GATE    file whose existence releases cs1-audit; default /tmp/cs1_audit_go.
#           Use GATE=/dev/null to run the audit without waiting.
#   DRIVER_LOG default /tmp/cscwd_all.log
set -uo pipefail
cd "$(dirname "$0")/.."

STAGES=${STAGES:-"cs1-small cs1-decomp cs1-audit-dry cs1-audit cs2 cs0-alpha cs3 cs3-code cs3b"}
GATE=${GATE:-/tmp/cs1_audit_go}
DRIVER_LOG=${DRIVER_LOG:-/tmp/cscwd_all.log}
ALPHA_FILE=results/execution/cs0_alpha_selection.json
FATAL='context length|maximum context|Traceback|CUDA out of memory|Engine core initialization failed'

log() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" >>"$DRIVER_LOG"; }

log "DRIVER START rev=$(git rev-parse --short HEAD) stages=[$STAGES] gate=$GATE"
if [ -n "$(git status --porcelain --untracked-files=no -- . ../psc)" ]; then
  log "ABORT: tracked files modified (would log a -dirty revision)"
  git status --short --untracked-files=no -- . ../psc >>"$DRIVER_LOG" 2>&1
  exit 1
fi

for st in $STAGES; do
  out=/tmp/$st.log
  case $st in
    cs1-audit)
      if [ ! -f "$GATE" ]; then
        log "GATE: waiting for $GATE before cs1-audit (planned volume is in /tmp/cs1-audit-dry.log)"
        until [ -f "$GATE" ]; do sleep 30; done
        log "GATE: released"
      fi ;;
    cs3|cs3-code|cs3b)
      if [ ! -f "$ALPHA_FILE" ]; then
        log "ABORT: $ALPHA_FILE missing, $st needs the alpha chosen by cs0-alpha"
        exit 1
      fi ;;
  esac

  : >"$out"
  log "START $st -> $out"
  t0=$(date +%s)
  if ! scripts/run_cscwd.sh "$st" >>"$out" 2>&1; then
    log "FAILED $st (exit non-zero), see $out"
    exit 1
  fi
  if grep -qiE "$FATAL" "$out"; then
    log "ABORT after $st: fatal pattern in $out: $(grep -ioE "$FATAL" "$out" | head -1)"
    exit 1
  fi
  if tail -1 results/logs/cscwd_commands.log | grep -q -- "-dirty"; then
    log "ABORT after $st: results/logs/cscwd_commands.log records a -dirty revision"
    exit 1
  fi
  log "DONE $st in $(( $(date +%s) - t0 ))s"
done
log "ALL DONE"
