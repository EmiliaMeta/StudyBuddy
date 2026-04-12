import requests, json

HEADERS = {"User-Agent": "study-planner-bot/1.0"}
BASE = "https://api.kth.se/api/kopps/v2"

r = requests.get(f"{BASE}/programmes/all", headers=HEADERS, timeout=15)
data = r.json()
print(f"Type: {type(data)}, length: {len(data)}")
print("Första item keys:", list(data[0].keys()) if data else "tom")
print("Första item:")
print(json.dumps(data[0], indent=2, ensure_ascii=False))