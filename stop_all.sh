#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$ROOT_DIR/.run"
BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"

stop_by_pid_file() {
  local pid_file="$1"
  local label="$2"

  if [[ ! -f "$pid_file" ]]; then
    echo "$label nao esta rodando (pid file ausente)."
    return
  fi

  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  if [[ -z "$pid" ]]; then
    rm -f "$pid_file"
    echo "$label nao esta rodando (pid invalido)."
    return
  fi

  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    sleep 1
    if kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" 2>/dev/null || true
    fi
    echo "$label parado (PID $pid)."
  else
    echo "$label ja estava parado."
  fi

  rm -f "$pid_file"
}

stop_by_pattern() {
  local pattern="$1"
  local label="$2"
  if pgrep -f "$pattern" >/dev/null 2>&1; then
    pkill -f "$pattern" || true
    sleep 1
    if pgrep -f "$pattern" >/dev/null 2>&1; then
      pkill -9 -f "$pattern" || true
    fi
    echo "$label parado por padrao de processo."
  fi
}

stop_by_pid_file "$BACKEND_PID_FILE" "Backend"
stop_by_pid_file "$FRONTEND_PID_FILE" "Frontend"

# Fallback: cobre casos em que os servicos foram iniciados manualmente.
stop_by_pattern "uvicorn app.main:app" "Backend"
stop_by_pattern "next dev" "Frontend"
