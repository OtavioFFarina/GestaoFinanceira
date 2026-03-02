import requests

url = "http://localhost:8000/api/ciclos"
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
