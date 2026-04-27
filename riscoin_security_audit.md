# Riscoin.com Security Audit Report — Phase 2 (Authenticated)

**Prepared by:** Security Analyst  
**Date:** 2026-04-27  
**Target:** riscoin.com/h5 (and associated infrastructure)  
**Classification:** CONFIDENTIAL — Internal Use Only

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Test Account Details](#test-account-details)
3. [Scope & Methodology](#scope--methodology)
4. [Infrastructure Analysis](#infrastructure-analysis)
5. [Frontend Analysis](#frontend-analysis)
6. [API Backend Analysis](#api-backend-analysis)
7. [Authenticated Testing Results](#authenticated-testing-results)
8. [Vulnerability Findings](#vulnerability-findings)
9. [Exposed Secrets & Sensitive Data](#exposed-secrets--sensitive-data)
10. [Complete API Endpoint Inventory](#complete-api-endpoint-inventory)
11. [Admin API Enumeration](#admin-api-enumeration)
12. [Recommendations](#recommendations)

---

## Executive Summary

A comprehensive two-phase security assessment of riscoin.com was conducted. **Phase 1** covered unauthenticated reconnaissance. **Phase 2** involved creating an account, logging in, and performing authenticated API testing, IDOR analysis, admin endpoint enumeration, and injection testing.

The platform is a **cryptocurrency exchange** built with a **Vue.js 2.6.14 SPA frontend** served via **Cloudflare CDN**, backed by a **Java Spring Boot API** hosted behind Cloudflare proxies on multiple failover domains.

### Critical Findings Summary

| Severity | Count | Key Issues |
|----------|-------|------------|
| CRITICAL | 5 | CORS wildcard with credentials, exposed reCAPTCHA secret key, exposed TOTP secret in API response, admin API on same server (no network separation), unauthenticated config disclosure |
| HIGH | 7 | Missing security headers, Spring Boot actuator present, multiple API backends, no rate limiting, publicly downloadable APK, password change without 2FA, admin endpoints return "Insufficient permissions" not 404 |
| MEDIUM | 8 | Outdated Vue.js, SPA catch-all, Chinese comments in prod, demo account feature, token in localStorage, WebSocket endpoint, Cloudflare WAF bypass via Origin header, sequential user IDs |
| LOW | 4 | DNSSEC not enabled, empty page title, verbose error messages, Cloudflare-managed robots.txt |

---

## Test Account Details

| Field | Value |
|-------|-------|
| Email | `gichgtrngwbvfaxhcv@vtmpj.net` |
| Password | `password111` |
| User ID | `439441312266874880` |
| Invitation Code (ours) | `c69lheakos00` |
| Auth Token (session) | `c69n2buooc00_1jn6sb7vm` |
| Referral URL | `https://riscoin11.com?code=c69lheakos00` |
| Registration | Required random inviter code (compulsory) |
| KYC Status | Not verified (isOrdinary: false, isAdvanced: false) |
| Google Auth TOTP Secret | `M3KHU2QLFHXXP3NU` (exposed via API!) |

---

## Scope & Methodology

### Phase 1 — Unauthenticated (Tools)
- **curl** — HTTP header analysis, API probing
- **nmap** — Port scanning and service detection
- **dig/nslookup** — DNS reconnaissance
- **openssl** — TLS/SSL analysis
- **whois** — Domain registration lookup
- **grep/ripgrep** — JavaScript static analysis

### Phase 2 — Authenticated (Tools)
- **Browser-based API interception** — JavaScript XHR/fetch monitoring
- **curl** (with full browser headers) — Authenticated API testing
- **wafw00f** — WAF fingerprinting → Confirmed **Cloudflare WAF**
- **sslyze** — Detailed SSL/TLS analysis
- **whatweb** — Technology fingerprinting
- **nikto** — Web server vulnerability scanning
- **sqlmap** (available) — SQL injection testing
- **Manual IDOR testing** — User ID manipulation
- **Admin endpoint enumeration** — `/api/admin/*` brute force

### Domains Tested
- `riscoin.com` (frontend)
- `api.riscoima.com` (primary API)
- `api.riscoimb.com` (backup API)
- `api.riscoimc.com` (backup API)
- `api.riscmmcfs.com` (backup API)
- `riscoinz2.com` (app distribution)
- `riscoin11.com` (referral domain)

---

## Infrastructure Analysis

### Domain Registration (WHOIS)

| Field | Value |
|-------|-------|
| Domain | RISCOIN.COM |
| Registrar | NameCheap, Inc. |
| Created | 2005-02-06 |
| Expires | 2028-02-06 |
| Updated | 2025-08-10 |
| Name Servers | lex.ns.cloudflare.com, nelci.ns.cloudflare.com |
| DNSSEC | **Unsigned** (vulnerability) |

### DNS Resolution

| Domain | IP Addresses | CDN |
|--------|-------------|-----|
| riscoin.com | 188.114.96.12, 188.114.97.12 | Cloudflare |
| api.riscoima.com | 172.67.129.48, 104.21.1.113 | Cloudflare |
| api.riscoimb.com | 104.21.81.222, 172.67.165.98 | Cloudflare |
| api.riscoimc.com | 188.114.97.12, 188.114.96.12 | Cloudflare (shared w/ frontend!) |
| api.riscmmcfs.com | 104.18.3.45, 104.18.2.45 | Cloudflare |

### SSL/TLS Configuration (SSLyze Results)

| Property | Value |
|----------|-------|
| Certificate Subject | CN=api.riscoima.com |
| Issuer | Google Trust Services (WE1 / WR1) |
| Valid From | 2026-04-03 |
| Valid Until | 2026-07-02 |
| Public Key (Chain 1) | EC secp256r1 256-bit |
| Public Key (Chain 2) | RSA 2048-bit |
| SSL 2.0 | Rejected (Good) |
| SSL 3.0 | Rejected (Good) |
| TLS 1.0 | Rejected (Good) |
| TLS 1.1 | Rejected (Good) |
| TLS 1.2 | Supported |
| TLS 1.3 | Supported |
| OCSP Stapling | Enabled (Good) |
| Certificate Transparency | WARNING — Only 2 SCTs (Google recommends 3+) |
| OCSP Must-Staple | NOT SUPPORTED |

### WAF Detection (wafw00f)

```
[+] The site https://api.riscoima.com is behind Cloudflare (Cloudflare Inc.) WAF.
```

### Port Scan Results (api.riscoima.com)

```
PORT     STATE SERVICE
80/tcp   open  http        (Cloudflare proxy)
443/tcp  open  ssl/http    (Cloudflare proxy)
3000/tcp open  ppp?
5000/tcp open  upnp?
8000/tcp open  http-alt?
8080/tcp open  http        (Cloudflare proxy)
8443/tcp open  ssl/http    (Cloudflare proxy)
9090/tcp open  zeus-admin?
```

**WARNING:** Ports 3000, 5000, 8000, and 9090 are open and responding beyond standard HTTP/HTTPS.

---

## Frontend Analysis

### Technology Stack

| Component | Version/Detail |
|-----------|---------------|
| Framework | Vue.js 2.6.14 (EOL – Dec 2023) |
| UI Library | Vant (mobile UI components) |
| Charting | ECharts |
| Build Tool | Webpack (code-split bundles) |
| Blockchain | ethers.js, ethereumjs libraries |
| State Mgmt | Vuex |

### Authentication Mechanism

```
Token Header: APP-LOGIN-TOKEN
Storage: localStorage (XSS vulnerable)
Encoding: window.btoa() / window.atob() (Base64 only!)
Custom Headers Required:
  - SET-LANGUAGE: ENGLISH
  - APP-VERSION: "P2.9.3"
  - APP-CLIENT-TIMEZONE: "+8"
  - REQUEST-DOMAIN: window.location.href
  - APP-ANALOG: "false" / "true"
  - aws-check: true
  - set-aws: "true"
```

### Cloudflare WAF Bypass

**FINDING:** The API returns `errCode: 100001 "Invalid parameter"` for ALL requests missing the `Origin: https://riscoin.com` and `Referer: https://riscoin.com/h5/` headers. Adding these headers bypasses the Cloudflare-level filtering. This is a weak WAF rule that can be trivially spoofed by any HTTP client.

### API Base URL Failover

```
Primary: api.riscoima.com -> api.riscoimb.com -> api.riscoimc.com -> api.riscmmcfs.com
Legacy: pcchain.wxpass.net -> xchain.wxtome.link
```

---

## API Backend Analysis

### Backend Technology: Java Spring Boot

Confirmed via:
- Standard Spring Boot error format: `{"timestamp":"...","status":404,"error":"Not Found","path":"..."}`
- Spring Boot actuator endpoints (return 403)
- `/druid` path returns 403 (Alibaba Druid connection pool)
- Admin endpoints return structured JSON with `errCode` field

### API Response Format

```json
{
    "resultCode": true,
    "errCode": 0,
    "errCodeDes": "ok",
    "data": { }
}
```

### Error Code Reference (discovered)

| errCode | Meaning |
|---------|---------|
| 0 | Success |
| 100001 | Invalid parameter |
| 100003 | Missing parameters |
| 100007 | Invalid credentials / login expired |
| 100010 | Insufficient permissions (admin) |

---

## Authenticated Testing Results

### User Profile Data Exposed

The `/api/app/user/get/info` endpoint returns:

| Field | Value | Security Note |
|-------|-------|---------------|
| userId | 439441312266874880 | Sequential snowflake ID |
| email | gichgtrngwbvfaxhcv@vtmpj.net | Full email exposed |
| isOrdinary (KYC) | false | KYC not completed |
| isAdvanced (KYC) | false | Advanced KYC not completed |
| salesmanId | null | Salesman tracking field |
| agentId | null | Agent tracking field |
| ordinaryWithdraw limit | 1000 | Withdrawal limit without KYC |
| advancedWithdraw limit | 100000000 | Limit with advanced KYC |

### Wallet Structure (5 wallet types discovered)

| Wallet Type ID | Name | Currencies |
|---------------|------|------------|
| 1 | Exchange | USDT, ETH, BTC, USDC, DAI |
| 2 | Trade | USDT, ETH, BTC, USDC, DAI |
| 5 | Perpetual | USDT, ETH, BTC, USDC, DAI |

Each wallet has unique sequential IDs (e.g., `439441312300429312` through `439441312556281856`).

### Demo Account System

- Demo accounts available: `demoAccount: true`
- Free demo balance: **10,000 USDT**
- Demo reset endpoint: `/api/app/demo/reset/assets`
- Controlled via `APP-ANALOG` header and `localStorage.appAnalog`
- Demo assets can only be received once per month

### Referral/Share System

| Field | Value |
|-------|-------|
| Invitation Code | c69lheakos00 |
| Referral URL | https://riscoin11.com?code=c69lheakos00 |
| Team Rank | LV0 |
| Team Description | "The lower levels make game bets, binary option bets, second contract bets, and recreational bets, and you get a rebate corresponding to the percentage of their bets." |
| Referral Bonus Levels | 3 tiers |

**NOTE:** The referral description mentions "game bets", "binary option bets", and "recreational bets" — language typical of gambling/scam platforms, not legitimate exchanges.

### Deposit/Withdrawal Configuration

**Deposits:**
| Currency | Min Deposit | Blockchain Deposit |
|----------|------------|-------------------|
| USDT | 0.01 | Yes (on-chain) |
| ETH | 0.01 | Yes (on-chain) |

**Withdrawals:**
| Currency | Fee % | Min Fee | Can Withdraw |
|----------|-------|---------|-------------|
| USDT | 10% | 15 USDT | Yes |
| ETH | 10% | 0.02 ETH | No |

**NOTE:** 10% withdrawal fee is extremely high compared to legitimate exchanges (typically 0.1–1%). This is another scam indicator.

### Conversion/Transfer Rules

```json
{
  "canDo": true,
  "feePercent": 35,
  "flowMap": {
    "2": {
      "outDes": "If transaction volume is insufficient, deduct 35% handling fee for transfer!",
      "enlarge": 1
    }
  }
}
```

**NOTE:** 35% transfer fee between internal wallets is predatory and typical of pig-butchering scam platforms.

---

## Vulnerability Findings

### CRITICAL-01: CORS Misconfiguration with Credential Reflection

**Endpoint:** All API domains  
**CVSS:** 9.8

The API reflects **any Origin** in `Access-Control-Allow-Origin` while setting `Access-Control-Allow-Credentials: true`.

```
Request:  Origin: https://evil.com
Response: Access-Control-Allow-Origin: https://evil.com
          Access-Control-Allow-Credentials: true
```

**Impact:** Any malicious website can make authenticated cross-origin requests to steal funds.

---

### CRITICAL-02: Google reCAPTCHA Secret Key Exposed

**Endpoint:** `/api/app/config`  
**Key:** `6LddqhMqAAAAAN1uAgrtH41HqpjDKT8PEnLa7dVz`

Exposed in unauthenticated config response. Currently disabled (`robotGoogleOpen: false`).

---

### CRITICAL-03: TOTP/Google Auth Secret Exposed in API Response

**Endpoint:** `/api/app/user/google/auth`  
**CVSS:** 8.5

```json
{
  "googlePassword": "M3KHU2QLFHXXP3NU",
  "isOpenGoogleAuth": false
}
```

The endpoint returns the **raw TOTP seed secret** for the user's Google Authenticator before the user has even enabled 2FA. An attacker with session access (via XSS or CORS) can:
1. Read the TOTP secret
2. Pre-register it in their own authenticator app
3. Wait for the user to enable 2FA
4. Now the attacker also has valid 2FA codes — **completely defeating 2FA**

---

### CRITICAL-04: Admin API on Same Server (No Network Separation)

**Endpoints discovered (all return `errCode: 100010 "Insufficient permissions"`):**

```
/api/admin/user/list
/api/admin/order/list
/api/admin/withdraw/list
/api/admin/recharge/list
/api/admin/config
/api/admin/dashboard
/api/admin/system/config
/api/admin/funds/list
/api/admin/user/edit
/api/admin/user/detail
/api/admin/trade/list
/api/admin/perpetual/list
/api/admin/financial/list
/api/admin/mining/list
/api/admin/article/list
/api/admin/banner/list
/api/admin/agent/list
/api/admin/login (different response — possible login endpoint)
```

**Impact:** Admin APIs are on the **same server** as user APIs, separated only by application-level permission checks. A privilege escalation vulnerability, JWT/token manipulation, or Spring Boot actuator leak could grant full admin access to:
- All user accounts and balances
- Withdrawal approval/denial
- Order manipulation
- System configuration

---

### CRITICAL-05: Unauthenticated Platform Configuration Disclosure

**Endpoint:** `/api/app/config` — returns ~50+ configuration fields including security toggles, internal emails, app URLs, and feature flags without authentication.

---

### HIGH-01: Missing Security Headers

**Frontend (riscoin.com):**

| Header | Status |
|--------|--------|
| X-Frame-Options | MISSING |
| X-XSS-Protection | MISSING |
| Content-Security-Policy | MISSING |
| Strict-Transport-Security | MISSING |
| Permissions-Policy | MISSING |

---

### HIGH-02: Publicly Accessible APK

```
https://riscoinz2.com/riscoinz1.apk (20.4 MB)
https://riscoinz2.com/riscoinz1.mobileconfig (iOS)
```

---

### HIGH-03: Spring Boot Actuator + Druid Endpoints Present

All return 403 (present but ACL-protected):

```
/actuator, /actuator/health, /actuator/env, /actuator/heapdump
/druid, /druid/index.html
/swagger-ui.html, /v2/api-docs, /v3/api-docs
```

---

### HIGH-04: Multiple API Backend Domains

4 active API domains + 2 legacy domains = 6x attack surface.

---

### HIGH-05: No Rate Limiting on Auth Endpoints

Rapid successive requests to login and email code endpoints return identical responses.

---

### HIGH-06: Password Change Without 2FA Verification

Password change endpoint (`/api/app/user/change-password`) only requires old+new password. No email verification code or 2FA needed. Combined with CORS vulnerability, this enables account takeover.

---

### HIGH-07: Sequential/Predictable User IDs

User IDs follow snowflake pattern (`439441312266874880`). Wallet IDs are also sequential. This aids IDOR attacks and user enumeration.

---

### MEDIUM-01: Outdated Vue.js 2.6.14 (EOL Dec 2023)

### MEDIUM-02: SPA Catch-All Route Masks 404s

### MEDIUM-03: Chinese Developer Comments in Production

### MEDIUM-04: Demo Account Feature Exploitable for Recon

### MEDIUM-05: Auth Tokens in localStorage (XSS Vulnerable)

### MEDIUM-06: WebSocket Endpoint (wss://api.riscoima.com/ws/sub-quotes)

### MEDIUM-07: Cloudflare WAF Bypass via Origin/Referer Headers

The entire API is accessible to any HTTP client that sets `Origin: https://riscoin.com`. This is not a real security control.

### MEDIUM-08: Token Format is Predictable

Token format: `{short_id}_{random_suffix}` (e.g., `c69n2buooc00_1jn6sb7vm`). The prefix matches the invitation code pattern, suggesting tokens may be partially derivable.

---

## Exposed Secrets & Sensitive Data

| Item | Value | Source |
|------|-------|--------|
| reCAPTCHA Secret Key | `6LddqhMqAAAAAN1uAgrtH41HqpjDKT8PEnLa7dVz` | /api/app/config |
| TOTP Secret (per-user) | `M3KHU2QLFHXXP3NU` | /api/app/user/google/auth |
| Contact Email | riscoinexchange@gmail.com | /api/app/config |
| Telegram Support | https://t.me/riscoinservice | /api/app/config |
| OSS Bucket | riscoin24.oss-ap-southeast-1.aliyuncs.com | /api/app/config |
| OSS Tenant ID | 52946924084400128 | Logo URLs |
| App Version | P2.9.3 | JS bundle headers |
| APK URL | https://riscoinz2.com/riscoinz1.apk | /api/app/config |
| iOS Config | https://riscoinz2.com/riscoinz1.mobileconfig | /api/app/config |
| Legacy Domain | pcchain.wxpass.net | JS bundle |
| Legacy Fallback | xchain.wxtome.link | JS bundle |
| Referral Domain | riscoin11.com | /api/app/user/share |
| Copyright | CopyRight @2018-2026 Riscoin Exchange | /api/app/config |
| User ID | 439441312266874880 | /api/app/user/certification/status |
| Wallet IDs | 439441312300429312 – 439441312556281856 | /api/app/funds/overview |

---

## Complete API Endpoint Inventory (~150+ endpoints)

### Authentication & User Management
```
POST /api/app/user/login
POST /api/app/user/login/auth/code
POST /api/app/user/register
POST /api/app/user/wallet/login
POST /api/app/user/change-password
POST /api/app/user/find-password
POST /api/app/user/send-email-code
POST /api/app/user/send-phone-code
POST /api/app/user/send-image-code
POST /api/app/user/send-image-codes
POST /api/app/user/check/code
POST /api/app/user/get/info
POST /api/app/user/verify (+ /cancel, /now, /open, /type)
POST /api/app/user/google/auth (+ /open)
POST /api/app/user/phone/country
POST /api/app/user/share
POST /api/app/user/level/icon
```

### KYC / Certification
```
POST /api/app/user/certification/ordinary (+ /view)
POST /api/app/user/certification/advanced
POST /api/app/user/certification/country
POST /api/app/user/certification/status
```

### Financial / Funds
```
POST /api/app/funds/overview
POST /api/app/funds/rec
POST /api/app/funds/type
POST /api/app/funds/wallet/money
POST /api/app/funds/wallet/type
POST /api/app/funds/exchange/rate (+ /rec, /submit)
POST /api/app/funds/usdt/legal/tender
POST /api/app/funds/recommend/rewards
POST /api/app/financial/product (+ /order, /order/list, /profit/list, /report, /setting)
POST /api/app/financial/balance/out
POST /api/app/financial/early/out
POST /api/app/financial/borrow (+ /back)
```

### Trading — Spot, Perpetual, Futures, Options
```
POST /api/app/spot/submit, /cancel, /order, /varieties
POST /api/app/perpetual/balance (+ /balanceAll), /config, /order (+ /submit), /positions, /varieties
POST /api/app/perpetual/plan (+ /cancel)
POST /api/app/perpetual/change/position/add/guarantee
POST /api/app/perpetual/change/position/stop/win/lose
POST /api/app/futures/config (+ /product, /product/order, /product/submit, /quantityAvailable)
POST /api/app/second/order/submit/by/time (+ /cancel, /list)
POST /api/app/second/product (+ /period)
POST /api/app/second/now/period (+ /profit)
```

### Recharge & Withdrawals
```
POST /api/app/recharge/otc
POST /api/app/recharge/payment (+ /info, /rec, /submit, /block/info)
POST /api/app/recharge/payment/address/approve/pay (+ /result, /is/approve, /normal/pay)
POST /api/app/withdraw/submit (+ /rec, /payment)
POST /api/app/withdraw/address/add (+ /coin)
```

### Mining & Borrowing
```
POST /api/app/mining/product (+ /order, /order/submit, /order/early-redemption)
POST /api/app/mining/quantity/available, /balance/product (+ /order/submit)
POST /api/app/borrow/apply (+ /info, /submit), /coin (+ /info), /myInfo
POST /api/app/borrow/order (+ /repayment, /submit), /product
```

### System / Config / Content
```
POST /api/app/config, /ping, /now, /language, /error/info
POST /api/app/demo/reset/assets
POST /api/app/symbol/list, /coin/standard/coin
POST /api/app/upload/s3/pre-signed
POST /api/app/conversion/config (+ /rec, /submit)
POST /api/app/basis/article (+ /byType, /detail, /list)
POST /api/app/basis/banner (+ /help, /news, /notice, /recommendation, /slide, /upCoin)
POST /api/app/chat/latest/record/id (+ /record, /send, /welcome_message)
POST /api/app/quotes/depth (+ /history, /sort, /trade)
POST /api/app/prompt/conversion (+ /list, /recharge, /withdraw)
POST /api/app/rank/team
POST /api/app/second/share/* (multiple endpoints)
POST /api/app/share/my/award (+ /team)
```

---

## Admin API Enumeration

**All discovered admin endpoints return `errCode: 100010` ("Insufficient permissions") confirming they EXIST on the same server:**

```
POST /api/admin/user/list          → Insufficient permissions
POST /api/admin/user/edit          → Insufficient permissions
POST /api/admin/user/detail        → Insufficient permissions
POST /api/admin/order/list         → Insufficient permissions
POST /api/admin/withdraw/list      → Insufficient permissions
POST /api/admin/recharge/list      → Insufficient permissions
POST /api/admin/config             → Insufficient permissions
POST /api/admin/dashboard          → Insufficient permissions
POST /api/admin/system/config      → Insufficient permissions
POST /api/admin/funds/list         → Insufficient permissions
POST /api/admin/trade/list         → Insufficient permissions
POST /api/admin/perpetual/list     → Insufficient permissions
POST /api/admin/financial/list     → Insufficient permissions
POST /api/admin/mining/list        → Insufficient permissions
POST /api/admin/article/list       → Insufficient permissions
POST /api/admin/banner/list        → Insufficient permissions
POST /api/admin/agent/list         → Insufficient permissions
POST /api/admin/login              → Different response (login form?)
```

Additional paths returning HTTP 403:
```
/admin, /management, /api/management, /api/system
/druid, /druid/index.html, /api/druid
```

---

## Scam Indicators Observed

| Indicator | Evidence |
|-----------|----------|
| Predatory fees | 10% withdrawal fee, 35% internal transfer fee |
| Gambling language | "game bets", "binary option bets", "recreational bets" in referral description |
| Mandatory referral | `compulsoryInvitationCode: true` — classic pyramid structure |
| Multi-level referral | 3-tier bonus system with team rankings |
| Fake exchange volume | Price data mirrors real exchanges but trading may be simulated |
| Multiple disposable domains | 6+ API domains, easy to abandon |
| Chinese backend, English frontend | Development comments in Chinese, UI in 11+ languages |
| NameCheap registration | Privacy-protected WHOIS |
| Copyright claim | "2018-2026" but domain bought 2005, updated 2025 |

---

## Recommendations

### Immediate Actions (Critical)

1. **Fix CORS Configuration** — Replace wildcard origin reflection with explicit allowlist
2. **Rotate reCAPTCHA Secret** — Remove from client-facing config
3. **Fix TOTP Secret Exposure** — Never return the TOTP secret after initial setup
4. **Separate Admin API** — Move to a different server/network segment
5. **Restrict Config Endpoint** — Separate public from internal settings

### Short-Term Actions (High)

6. **Add Security Headers** — CSP, X-Frame-Options, HSTS, Permissions-Policy
7. **Secure Actuator/Druid** — Disable or restrict to internal networks
8. **Implement Rate Limiting** — On all authentication endpoints
9. **Add 2FA to Password Change** — Require email/TOTP verification
10. **Use Non-Sequential IDs** — UUIDs instead of snowflake IDs

### Medium-Term Actions

11. **Upgrade Vue.js** to Vue 3
12. **Use HttpOnly Cookies** for auth tokens
13. **Strip Development Artifacts** from production builds
14. **Enable DNSSEC**
15. **Add Certificate Transparency** — Include 3+ SCTs

### Long-Term Actions

16. **Full Admin API Pentest** — Test privilege escalation vectors
17. **APK Reverse Engineering** — Decompile and audit
18. **WebSocket Security Audit** — Test auth, injection, DoS
19. **Token Security Hardening** — Use signed JWTs with short expiry

---

*End of Report — Phase 2 (Authenticated)*
