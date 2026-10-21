#!/usr/bin/env bash

if [ -s "$HOME/.nvm/nvm.sh" ]; then
  export NVM_DIR="$HOME/.nvm"
  \. "$NVM_DIR/nvm.sh"
fi

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
VENV_DIR="$ROOT_DIR/.venv"
COMPOSE_FILE="$ROOT_DIR/docker-compose.postgres.yml"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
RUN_DIR="$ROOT_DIR/.run"
BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"
BACKEND_LOG_FILE="$RUN_DIR/backend.log"
FRONTEND_LOG_FILE="$RUN_DIR/frontend.log"
BACKEND_PORT_FILE="$RUN_DIR/backend.port"

port_is_busy() {
  local port="$1"
  python3 - "$port" <<'PY'
import socket
import sys

port = int(sys.argv[1])
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(0.2)
try:
  status = sock.connect_ex(("127.0.0.1", port))
  if status == 0:
    print("busy")
  else:
    print("free")
except OSError:
  print("busy")
finally:
  sock.close()
PY
}

find_backend_port() {
  local candidate
  for candidate in $(seq 8001 8015); do
    if [[ "$(port_is_busy "$candidate")" == "free" ]]; then
      echo "$candidate"
      return 0
    fi
  done

  echo "Nao encontrei uma porta livre entre 8001 e 8015 para o backend."
  exit 1
}

docker_cmd() {
  if command -v docker >/dev/null 2>&1; then
    docker "$@"
    return
  fi

  if command -v flatpak-spawn >/dev/null 2>&1; then
    flatpak-spawn --host docker "$@"
    return
  fi

  echo "Docker nao encontrado no PATH."
  exit 1
}

ensure_backend_env() {
  if [[ ! -f "$BACKEND_DIR/.env" ]]; then
    cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
  fi
}

ensure_frontend_env() {
  printf 'NEXT_PUBLIC_API_URL=http://localhost:%s\n' "$BACKEND_PORT" > "$FRONTEND_DIR/.env.local"
}

ensure_venv() {
  if [[ ! -x "$VENV_DIR/bin/uvicorn" ]]; then
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install -r "$BACKEND_DIR/requirements.txt"
  fi
}

ensure_frontend_deps() {
  if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
    (cd "$FRONTEND_DIR" && npm install)
  fi
}

is_pid_running() {
  local pid="$1"
  kill -0 "$pid" 2>/dev/null
}

cleanup_stale_pid_files() {
  if [[ -f "$BACKEND_PID_FILE" ]]; then
    local pid
    pid="$(cat "$BACKEND_PID_FILE" 2>/dev/null || true)"
    if [[ -z "$pid" ]] || ! is_pid_running "$pid"; then
      rm -f "$BACKEND_PID_FILE"
    fi
  fi

  if [[ -f "$FRONTEND_PID_FILE" ]]; then
    local pid
    pid="$(cat "$FRONTEND_PID_FILE" 2>/dev/null || true)"
    if [[ -z "$pid" ]] || ! is_pid_running "$pid"; then
      rm -f "$FRONTEND_PID_FILE"
    fi
  fi
}

ensure_not_already_running() {
  cleanup_stale_pid_files

  if [[ -f "$BACKEND_PID_FILE" ]]; then
    local pid
    pid="$(cat "$BACKEND_PID_FILE")"
    echo "Backend ja esta rodando (PID $pid)."
    echo "Use ./stop_all.sh para parar antes de iniciar novamente."
    exit 1
  fi

  if [[ -f "$FRONTEND_PID_FILE" ]]; then
    local pid
    pid="$(cat "$FRONTEND_PID_FILE")"
    echo "Frontend ja esta rodando (PID $pid)."
    echo "Use ./stop_all.sh para parar antes de iniciar novamente."
    exit 1
  fi
}

start_postgres() {
  docker_cmd compose -f "$COMPOSE_FILE" up -d
}

ensure_ports_free() {
  local backend_port_state
  local frontend_port_state
  backend_port_state="$(port_is_busy "$BACKEND_PORT")"
  frontend_port_state="$(port_is_busy "$FRONTEND_PORT")"

  if [[ "$backend_port_state" == "busy" ]]; then
    echo "Porta $BACKEND_PORT em uso. Finalize o processo atual e rode novamente."
    echo "Sugestao: pkill -f 'uvicorn app.main:app'"
    exit 1
  fi

  if [[ "$frontend_port_state" == "busy" ]]; then
    echo "Porta $FRONTEND_PORT em uso. Finalize o processo atual e rode novamente."
    echo "Sugestao: pkill -f 'next dev'"
    exit 1
  fi
}

start_backend() {
  (
    cd "$BACKEND_DIR"
    nohup "$VENV_DIR/bin/uvicorn" app.main:app --reload --host 0.0.0.0 --port "$BACKEND_PORT" >"$BACKEND_LOG_FILE" 2>&1 &
    echo $! >"$BACKEND_PID_FILE"
  )
}

start_frontend() {
  (
    cd "$FRONTEND_DIR"
    nohup npm run dev >"$FRONTEND_LOG_FILE" 2>&1 &
    echo $! >"$FRONTEND_PID_FILE"
  )
}

mkdir -p "$RUN_DIR"

ensure_backend_env
BACKEND_PORT="$(find_backend_port)"
printf '%s\n' "$BACKEND_PORT" > "$BACKEND_PORT_FILE"
ensure_frontend_env
ensure_venv
ensure_frontend_deps
start_postgres
ensure_not_already_running
ensure_ports_free
start_backend
start_frontend

echo "Backend:  http://127.0.0.1:$BACKEND_PORT/health"
echo "Frontend: http://127.0.0.1:3000"
echo "Porta do backend escolhida: $BACKEND_PORT"
echo "Logs backend:  $BACKEND_LOG_FILE"
echo "Logs frontend: $FRONTEND_LOG_FILE"
echo "Para parar backend e frontend: ./stop_all.sh"