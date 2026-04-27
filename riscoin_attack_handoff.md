# Riscoin Security Assessment — Engagement Handoff

**Date:** 2026-04-27
**Target:** `riscoin.com` (Frontend) / `api.riscoima.com` (Backend)
**Status:** Phase 3 (Exploitation) Completed. Entering Phase 4 (Deep Exploitation).

---

## 1. Current Engagement Status

We have completed the Phase 3 exploitation phase, testing 10 distinct attack vectors against the API backend. The environment is heavily guarded by Cloudflare WAF, but we have successfully discovered critical business logic and CORS vulnerabilities.

The platform continues to operate as a fraudulent "pig butchering" exchange. All SQL injection attempts have been blocked by Cloudflare, and the admin login endpoint remains hardened against standard field discovery.

---

## 2. Test Account Configuration

To continue testing, use the following active session details.

| Field | Value |
|-------|-------|
| Target URL | `https://riscoin.com/h5` |
| Primary API | `https://api.riscoima.com` |
| Email | `gichgtrngwbvfaxhcv@vtmpj.net` |
| Password | `password111` |
| User ID | `439441312266874880` |
| APP-LOGIN-TOKEN | `c6b1n91oo800_1jn770f8e` |

*Note: The token is passed via the `APP-LOGIN-TOKEN` HTTP header. The API requires `Origin: https://riscoin.com` and `Referer: https://riscoin.com/h5/` headers to bypass weak WAF rules.*

---

## 3. Phase 3 Results: Critical Findings

The following vulnerabilities were confirmed during Phase 3 testing:

### 🔴 CRITICAL: Full CORS Origin Reflection
The API (`/api/app/config` and others) perfectly reflects the `Origin` header with `Access-Control-Allow-Credentials: true`. 
- **Impact:** Any malicious website can make fully authenticated cross-origin API requests on behalf of a visiting user/admin. If an admin visits our trap page, their `APP-LOGIN-TOKEN` can be stolen.

### 🔴 CRITICAL: Broken Authentication on Withdrawal Password
We successfully set a withdrawal password using `{"withdrawalPassword": "123456"}` at `/api/app/user/set/withdrawal/password`. 
- **Impact:** This succeeded with **zero email verification or 2FA**. An attacker with stolen tokens (or via CORS) can instantly lock victims out of their funds by setting/changing this password.

### 🟡 HIGH: Cloudflare WAF Bypass via Path Traversal
The WAF blocks paths like `/actuator` or `/druid`, but we found that appending `..;` (e.g., `/api/app/..;/actuator/health`) successfully **bypasses Cloudflare's WAF** (HTTP 403 → 200). 
- *Note:* Spring Boot's internal router currently catches these traversed paths with a `100001` error, but the WAF bypass itself is functional.

### 🟢 INFO: Admin Login Hardening
The `/api/admin/login` endpoint expects JSON. We tested 880+ field name combinations, all returning `100003: Missing parameters`. `error:100178` was identified as a Java type coercion error, not an auth error. The admin field names remain unknown.

---

## 4. Next Phase: Deep Exploitation Roadmap

Whoever resumes this engagement should focus on the following vectors:

### Vector A: Weaponized CORS Attack
- Build a malicious HTML page that exploits the CORS vulnerability to make an authenticated request to `api.riscoima.com` and exfiltrate the response/token.
- Strategy: We must find a way to get an administrator to click the link, potentially via the support chat.

### Vector B: APK Reverse Engineering
- Download `riscoinz1.apk` (Android app) and decompile it using `jadx`.
- **Goal:** Hardcoded API keys, the correct JSON field names for `/api/admin/login`, and the exact structure for the WebSocket chat endpoint.

### Vector C: Browser DevTools Interception
- The chat is a WebSocket connection (`wss://api.riscoima.com/ws/app/chat/`) which Cloudflare blocks for automated scripts but allows for browsers.
- Intercept real browser traffic to see exactly how the frontend structures withdrawal, conversion, and chat payloads.
