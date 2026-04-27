# Riscoin.com Security Audit — Additional Analysis

**Prepared by:** Security Analyst  
**Date:** 2026-04-27  
**Classification:** CONFIDENTIAL — Internal Use Only

This document supplements the main security audit report with deeper conceptual analysis regarding the platform's fund flow, theoretical exploitation vectors, administrative architecture, and database management strategies.

---

## 1. External Funds Handling & Workflow

The platform operates similarly to a typical Centralized Exchange (CEX), but with distinct "trap" mechanisms common in fraudulent platforms.

### Deposits (Recharging)
* **Address Generation:** Users request deposit addresses via endpoints like `/api/app/recharge/payment/block/info` for standard chains (USDT on TRC20/ERC20, ETH).
* **Manual Verification:** Instead of purely automated blockchain node watchers, the platform contains endpoints like `/api/app/recharge/payment/submit`. In many scam platforms, users must manually submit transaction hashes or screenshots for an admin to verify.
* **Internal Crediting:** Once verified (via the admin panel `/api/admin/recharge/list`), the actual cryptocurrency remains in the operator's overarching wallet. The user's internal database balance is simply updated with an "IOU."

### Internal Holding ("The Trap")
* **Segmented Wallets:** Funds are locked into isolated database wallets (Exchange, Trade, Perpetual).
* **Predatory Conversion:** The `/api/app/conversion/config` endpoint reveals a staggering **35% transfer fee** for moving funds between a user's own internal wallets unless arbitrary "trading volume" metrics are met. This is explicitly designed to force users to gamble or trade rather than hold or withdraw.

### Withdrawals (The Exit Block)
* **Predatory Fees:** The platform charges an absurdly high **10% withdrawal fee** (minimum 15 USDT) on the way out.
* **Admin Gatekeeping:** Withdrawals do not trigger a hot wallet smart contract. Instead, requests queue in the backend (`/api/admin/withdraw/list`). A human administrator must manually approve the transaction, giving them the power to infinitely delay, deny, or demand additional "verification taxes."
* **KYC Hostage:** Unverified accounts face strict withdrawal limits (capped at 1,000). To withdraw larger amounts, users must surrender highly sensitive identity documents ("Advanced KYC"), which are then harvested.

---

## 2. API Exploitation & Balance Manipulation

In theory, the platform is susceptible to standard business logic vulnerabilities, though exploiting them will not result in extracting real funds.

* **Parameter Tampering:** If the backend carelessly trusts client-side input during a trade or deposit submission (e.g., modifying the `"amount"` or `"price"` JSON field), an attacker could artificially inflate their balance.
* **Race Conditions (TOCTOU):** Submitting multiple simultaneous withdrawal or transfer requests could potentially bypass balance checks if the database lacks proper row-level locking or transaction isolation.
* **Privilege Escalation:** If an attacker finds an authentication bypass or JWT manipulation flaw to access the admin APIs (`/api/admin/user/edit`), they could arbitrarily edit balances.
* **The Catch (Database Reality):** Even if an attacker successfully forces the API to display a $10,000,000 balance, the withdrawal architecture prevents cashing out. The manual withdrawal queue ensures a human admin will review the request, realize no matching blockchain deposit exists, and terminate the account. The exploited numbers are purely superficial.

---

## 3. Administrator Panel Architecture

The backend infrastructure exposes critical operational details about how the administrators run the platform.

* **No Network Separation:** The most severe architectural flaw is that the Admin APIs are hosted on the exact same public server as the user APIs (`https://api.riscoima.com/api/admin/...`). They are separated only by application-level permission checks (returning `100010: Insufficient permissions` to standard users).
* **Complete Manual Control:** Endpoints like `/api/admin/withdraw/list`, `/api/admin/recharge/list`, and `/api/admin/funds/list` prove the platform is entirely manually operated. Admins have god-mode over the financial ledger.
* **Pyramid/Agent Management:** The `/api/admin/agent/list` endpoint confirms the platform operates a tiered affiliate/agent system, allowing admins to track and manage the promoters luring victims into the scheme.
* **Frontend Access Protection:** While the APIs are exposed, visual endpoints like `/admin`, `/management`, and the login form at `/api/admin/login` exhibit different responses (like HTTP 403 Forbidden), indicating that Cloudflare or WAF rules restrict visual access to unauthorized IPs.

---

## 4. Database Management & Data Handling

The platform's technical footprint provides a clear map of its data layer, identifying a standard Chinese enterprise Java stack.

* **Database Stack (Java + MySQL):** The presence of the `/druid` endpoint (Alibaba Druid JDBC connection pool manager) strongly indicates a relational database, almost certainly MySQL.
* **Spring Data JPA:** Responses containing `pageable`, `totalElements`, and `sort` objects perfectly match the default JSON serialization of Spring Data JPA, confirming the ORM technology in use.
* **Snowflake ID Generation:** Primary keys (e.g., `439441312266874880`) are generated using a distributed Snowflake ID algorithm and stored as `BIGINT`. This prevents attackers from easily estimating the total user base.
* **User Tracking & Hierarchy:** The database stores registration IPs, login IPs (with geolocation), and uses relational foreign keys (`superiorId`, `salesmanId`, `agentId`) to map out the affiliate pyramid scheme.
* **External File Storage:** The database does not store binary blobs for KYC images or avatars. Instead, files are uploaded directly to Alibaba Cloud Object Storage Service (bucket: `riscoin24.oss-ap-southeast-1.aliyuncs.com`) via pre-signed URLs generated by `/api/app/upload/s3/pre-signed`. The database simply stores the resulting URL.
* **Secret Handling Flaws:** While passwords appear to be Base64-encoded in transit and likely salted/hashed at rest (indicated by a `salt` column in the user schema), the platform critically fails by returning Google Authenticator TOTP secrets in plain text API responses.

---

*End of Document*
