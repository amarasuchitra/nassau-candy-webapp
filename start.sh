#!/usr/bin/env sh
# Start the Nassau Candy web app locally (Mac/Linux): http://localhost:8000
set -e
cd "$(dirname "$0")"
if [ ! -f .venv-installed ]; then
  echo "First run: setting up, this takes a minute or two..."
  python3 -m venv .venv
  .venv/bin/python -m pip install --upgrade pip >/dev/null
  .venv/bin/python -m pip install -r requirements.txt
  touch .venv-installed
fi
PORT=$(.venv/bin/python -m backend.free_port 8000)
echo "Dashboard: http://127.0.0.1:$PORT    API docs: http://127.0.0.1:$PORT/docs"
( sleep 4; (command -v open >/dev/null && open "http://127.0.0.1:$PORT") || (command -v xdg-open >/dev/null && xdg-open "http://127.0.0.1:$PORT") || true ) &
exec .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port "$PORT"
