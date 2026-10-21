from pathlib import Path

import requests


def get_backend_port() -> str:
    port_file = Path(__file__).resolve().parents[1] / ".run" / "backend.port"
    if port_file.exists():
        port = port_file.read_text(encoding="utf-8").strip()
        if port:
            return port
    return "8001"

url = f"http://localhost:{get_backend_port()}/api/ciclos"
payload = {
    "usuario_id": "00000000-0000-0000-0000-000000000001",
    "ano": 2026,
    "mes": 3,
    "renda_total": 1621,
    "observacoes": "test"
}
try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
