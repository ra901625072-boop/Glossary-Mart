# E-GLOSSARY MART — FINAL COMPREHENSIVE SECURITY AUDIT & HARDENING REPORT

**Audit Date:** September 2026  
**Auditor / Security Architect:** Google Deepmind Antigravity Security Team  
**Scope:** Complete E-Glossary / E-Grossary Mart Application Lifecycle & Expert Re-Audit  
**Compliance Standards:** OWASP Top 10 (2021), OWASP API Security Top 10 (2023), ASVS v4.0.3, NIST SP 800-63B  
**Test Suite Status:** 44 / 44 Tests Passing (100% Green)

---

## 1. Executive Summary

A comprehensive, zero-trust security audit and architectural hardening were performed across the entire **E-Grossary / E-Glossary Mart** codebase (`d:\mart\mart`), followed by an exhaustive second-pass expert re-audit. Prior to this engagement, the application contained critical vulnerabilities spanning authentication bypasses, insecure direct object references (IDOR/BOLA) in financial workflows, wholesale cost and proprietary supplier data leakage, stored cross-site scripting (XSS), insecure file uploads, CSV formula injection, wildcard CORS policies, and denial-of-service crash triggers. In the second pass, additional subtle edge-case vulnerabilities—including API content negotiation status code mismatches, cumulative credit limit bypasses, unauthenticated background restock concurrency risks, and unlogged financial balance clearances—were identified and systematically resolved.

Every identified vulnerability has been structurally mitigated using defense-in-depth, least privilege, and secure-by-default architecture. Automated regression tests (`tests/test_security_audit.py`) verify the durability of all fixes. The existing 28 system and integration tests continue to pass without regression.

### Security Posture Comparison

| Dimension | Before Audit | After Hardening |
|---|---|---|
| **Authentication & 2FA** | 2FA was completely bypassed in Web and API login flows; credentials immediately created active sessions. | Enforced in all entrypoints. Session fixation protected (`session.clear()`). Credentials staged until TOTP verification. |
| **Payment & Checkout** | Any user could initiate Stripe sessions or simulate payment success for arbitrary orders (IDOR/BOLA). | Strict user ownership verification, state machine constraints, Stripe amount matching, and order metadata binding. |
| **Data Privacy & APIs** | Wholesale cost price, supplier identities, and profit margins leaked in public product JSON responses. | Dual-tier role serialization (`is_admin=False` by default) redacting sensitive business metrics from public/customer responses. |
| **Frontend Security** | User inputs, product titles, order addresses, and customer names were concatenated directly into `innerHTML`. | Context-aware HTML entity escaping applied uniformly across `admin.js`, `customer.js`, and `homepage.js`. |
| **File Storage & Uploads** | Only checked file extensions; timestamp-based naming; vulnerable to polyglots and directory traversal. | Validates magic bytes, enforces Pillow image integrity checks, and assigns cryptographic UUID filenames (`uuid4.hex`). |
| **Export Security** | Raw sales data written to CSV without sanitization, exposing admins to formula injection (CWE-1236). | `sanitize_csv_cell` neutralizes all active spreadsheet formula prefixes (`=`, `+`, `-`, `@`, `\t`, `\r`). |
| **CORS & Network** | Open regex `.*\.vercel\.app` allowed any arbitrary attacker with a Vercel project to access credentials and APIs. | Restricted strict regex `^https:\/\/glossary-mart(-[a-zA-Z0-9_-]+)?\.vercel\.app$` scoped exclusively to official app domains. |
| **Transport & Headers** | Missing HSTS; open wildcard `img-src *` in Content Security Policy; weak frame protection. | Strict-Transport-Security (1 year HSTS), frame-ancestors 'self', and tightened CSP img-src allowlist. |
| **Rate Limiting** | Authentication endpoints had no brute-force or credential stuffing throttles. | Flask-Limiter decorators applied to `/api/auth/login`, `/auth/register`, `/api/auth/verify-2fa`, and password reset routes. |

---

## 2. Threat Matrix & Vulnerability Summary

| ID | Title | Severity | OWASP (2021) | OWASP API (2023) | Status |
|---|---|---|---|---|---|
| **VULN-01** | Two-Factor Authentication (2FA) Complete Bypass | **CRITICAL** | A07: Identification & Auth Failures | API2: Broken Authentication | **RESOLVED** |
| **VULN-02** | Payment Session Creation Insecure Direct Object Reference (BOLA/IDOR) | **CRITICAL** | A01: Broken Access Control | API1: Broken Object Level Auth | **RESOLVED** |
| **VULN-03** | Unverified Payment Gateway Callback & State Tampering | **HIGH** | A04: Insecure Design | API6: Unrestricted Resource Access | **RESOLVED** |
| **VULN-04** | Stored Cross-Site Scripting (XSS) via InnerHTML Template Injection | **HIGH** | A03: Injection | API8: Security Misconfiguration | **RESOLVED** |
| **VULN-05** | Overly Permissive Wildcard CORS Configuration | **HIGH** | A05: Security Misconfiguration | API8: Security Misconfiguration | **RESOLVED** |
| **VULN-06** | Wholesale Cost, Supplier, and Profit Margin Data Leakage | **MEDIUM** | A01: Broken Access Control | API3: Broken Object Property Auth | **RESOLVED** |
| **VULN-07** | Insecure File Upload & Predictable Storage Filenames | **MEDIUM** | A04: Insecure Design | API8: Security Misconfiguration | **RESOLVED** |
| **VULN-08** | Missing Rate Limiting on Authentication & Indefinite Password Reset Tokens | **MEDIUM** | A07: Identification & Auth Failures | API4: Unrestricted Resource Consumption | **RESOLVED** |
| **VULN-09** | Udhar Store Credit Abuse & Unverified Checkout Exploitation | **MEDIUM** | A04: Insecure Design | API6: Unrestricted Resource Access | **RESOLVED** |
| **VULN-10** | Database Relationship Misnaming Causing Silent POS & Cart Corruptions | **LOW** | A04: Insecure Design | API8: Security Misconfiguration | **RESOLVED** |
| **VULN-11** | CSV Formula Injection (CWE-1236) in Financial Reporting | **LOW** | A03: Injection | API8: Security Misconfiguration | **RESOLVED** |
| **VULN-12** | Missing Service Method & Unhandled Runtime Exceptions (OrderService) | **LOW** | A05: Security Misconfiguration | API8: Security Misconfiguration | **RESOLVED** |
| **VULN-13** | CSP Wildcard Exposure & Missing HSTS Enforcement | **LOW** | A05: Security Misconfiguration | API8: Security Misconfiguration | **RESOLVED** |
| **RE-AUDIT-01** | API Decorator 302 Redirection Instead of 401/403 Status Codes | **MEDIUM** | A01: Broken Access Control | API2: Broken Authentication | **RESOLVED** |
| **RE-AUDIT-02** | Cumulative Store Credit (Udhar) Limit Bypass Vulnerability | **HIGH** | A04: Insecure Design | API6: Unrestricted Resource Access | **RESOLVED** |
| **RE-AUDIT-03** | Administrator Role Separation on Online Checkout Endpoints | **LOW** | A01: Broken Access Control | API5: Broken Function Level Auth | **RESOLVED** |
| **RE-AUDIT-04** | Race Conditions & Unlogged Stock Mutations in Admin Purchases | **MEDIUM** | A04: Insecure Design | API8: Security Misconfiguration | **RESOLVED** |
| **RE-AUDIT-05** | Missing Audit Trail on Customer Credit Settlements | **LOW** | A09: Security Logging & Monitoring | API8: Security Misconfiguration | **RESOLVED** |
| **RE-AUDIT-06** | Single HTTP Method Constraint on API Session Termination | **INFO** | A07: Identification & Auth Failures | API2: Broken Authentication | **RESOLVED** |

---

## 3. Remediation Details by Vulnerability

### VULN-01: Two-Factor Authentication (2FA) Enforcement
- **Root Cause:** Both web (`backend/routes/auth.py`) and REST API (`backend/routes/api/auth.py`) login handlers inspected `user.two_factor_enabled` but executed `login_user(user)` immediately prior to code verification, granting full authenticated privileges before TOTP verification.
- **Fix:** Login handlers now verify whether `user.two_factor_enabled` is active. If true, credentials are staged in a transient `session["2fa_user_id"]` with a strict 5-minute expiry (`2fa_expires_at`). The user is NOT logged in. Authentication is finalized only upon valid TOTP verification at `/security/verify-2fa` or `/api/auth/verify-2fa`. Added `session.clear()` to prevent session fixation.

### VULN-02 & VULN-03: Payment BOLA/IDOR & Gateway Verification
- **Root Cause:** `/create-checkout-session/<order_id>` and `/payment/success/<order_id>` did not verify that `order.user_id == current_user.id`. Any authenticated user could create a Stripe session for another customer's order or trigger simulated payment completion. Furthermore, payment completion failed to verify that the Stripe session payment total matched the order total.
- **Fix:** Added strict ownership checks (`order.user_id != current_user.id -> 403 Forbidden`). Order state validation prohibits payments for paid, cancelled, or returned orders. Stripe session creation embeds metadata (`order_id`, `user_id`) and client reference IDs. Gateway callback validates matching order ID and amount in cents. Simulation fallback is blocked in production environments.

### VULN-04: Stored Cross-Site Scripting (XSS)
- **Root Cause:** Client-side JavaScript engines (`frontend/static/js/admin.js`, `customer.js`, and `homepage.js`) directly interpolated customer names, shipping addresses, telephone numbers, product titles, category descriptions, and activity logs into `.innerHTML` template literals without HTML entity encoding.
- **Fix:** Implemented a uniform `escapeHTML(str)` utility across all frontend scripts replacing `&`, `<`, `>`, `"`, and `'`. All dynamic string interpolations in table bodies, product cards, modal dialogues, and live search dropdowns are wrapped with `escapeHTML()`.

### VULN-05: Wildcard CORS Policy Hardening
- **Root Cause:** `backend/config.py` included `r"^https:\/\/.*\.vercel\.app$"` in `CORS_ALLOWED_ORIGINS`, allowing any malicious actor with an arbitrary Vercel deployment to initiate credentialed cross-origin requests (`supports_credentials=True`).
- **Fix:** Replaced open wildcard pattern with `r"^https:\/\/glossary-mart(-[a-zA-Z0-9_-]+)?\.vercel\.app$"`, restricting cross-origin access strictly to official production and preview branch deployments of Glossary Mart.

### VULN-06: Wholesale Cost & Supplier Data Leakage
- **Root Cause:** `Product.to_dict()` and `OrderItem.to_dict()` serialized `cost_price`, `profit_margin`, `minimum_stock_alert`, `supplier_name`, and item `profit` unconditionally into JSON objects served by public `/api/products` and `/api/categories` endpoints.
- **Fix:** Introduced role-aware serialization: `to_dict(is_admin=False)` defaults to redacting sensitive proprietary financial metrics. Admin routes explicitly request `is_admin=True` to retain ERP dashboard analytics while preserving public data privacy.

### VULN-07: Insecure File Uploads & UUID Storage Naming
- **Root Cause:** Product image upload in `backend/services/storage_service.py` relied solely on extension verification and timestamp prefixing (`timestamp_filename`), risking polyglot code execution, file overwrite, and directory traversal.
- **Fix:** Created `backend/utils/files.py::validate_image_file` performing three-layer defense: extension allowlisting (`png`, `jpg`, `jpeg`, `gif`, `webp`), magic byte header inspection, and Pillow deep image verification (`Image.open().verify()`). Files are saved with cryptographically random UUIDs (`uuid.uuid4().hex`) to eliminate path traversal and collisions.

### VULN-08: Rate Limiting & Token Lifetime
- **Root Cause:** Sensitive authentication routes had no request rate limiting. Password reset tokens embedded in URLs had no expiration checks.
- **Fix:** Decorated `/api/auth/login` (5/min), `/api/auth/register` (3/min), `/api/auth/verify-2fa` (10/min), and `/api/auth/profile` (20/min) with Flask-Limiter. Token generation in `backend/routes/security.py` now embeds UNIX timestamps (`token.{timestamp}`), enforcing a 15-minute expiration ceiling.

### VULN-09: Udhar (Store Credit) Abuse
- **Root Cause:** Checkout accepted `UDHAR` payment method without enforcing customer verification status or credit balance ceilings.
- **Fix:** `backend/routes/customer.py` and `backend/services/order_service.py` enforce that Udhar transactions require `user.is_verified=True` and a cumulative credit ceiling `< ₹5000`.

### VULN-11: CSV Formula Injection Prevention
- **Root Cause:** `backend/services/export_service.py::generate_sales_csv` exported product names and sales data directly into CSV rows without formula sanitization.
- **Fix:** Implemented `sanitize_csv_cell(val)` which prefixes any cell starting with active spreadsheet formula operators (`=`, `+`, `-`, `@`, `\t`, `\r`) with a single apostrophe (`'`), rendering formula execution inert in Excel, Google Sheets, and Calc.

### VULN-12: Missing Methods & Runtime Crash Prevention
- **Root Cause:** Missing `OrderService.create_order_from_cart` caused runtime crashes on checkout; mismatched attribute `order.items` (correct: `order.order_items`) crashed order retrieval; missing `url_for` import in `admin/sales.py`.
- **Fix:** Implemented `OrderService.create_order_from_cart`; standardized relationship access to `order.order_items`; imported `url_for` in `backend/routes/admin/sales.py`.

### VULN-13: Security Headers & CSP Tightening
- **Root Cause:** `Content-Security-Policy` contained `img-src *` wildcard; missing `Strict-Transport-Security` (HSTS) header.
- **Fix:** Refined CSP `img-src` to explicitly trusted sources (`'self' data: blob: https://images.unsplash.com https://*.s3.amazonaws.com https://cdn.jsdelivr.net https://api.qrserver.com`); added `frame-ancestors 'self'`; attached `Strict-Transport-Security: max-age=31536000; includeSubDomains` in production environments.

### RE-AUDIT-01: API Authentication Content Negotiation (RFC 7235 & OWASP API2)
- **Root Cause:** `@admin_required` and `@customer_required` returned HTTP 302 redirects to HTML login pages even for JSON/AJAX API requests, breaking client-side parsing and violating REST conventions.
- **Fix:** Added `_is_api_or_json_request()` inspection to decorators and `restrict_public_routes`. API clients receive structured `401 Unauthorized` or `403 Forbidden` JSON responses, while web browser requests continue receiving seamless 302 redirects.

### RE-AUDIT-02: Cumulative Store Credit (Udhar) Limit Enforcement
- **Root Cause:** Checking `if current_credit > 5000` allowed a customer with ₹4,800 or ₹4,999 in existing debt to place unlimited orders because the condition checked starting balance instead of cumulative balance post-order.
- **Fix:** Enforced `if (current_credit + float(total_amount)) > 5000:` across `OrderService.process_checkout`, `OrderService.create_order_from_cart`, and `customer.checkout`.

### RE-AUDIT-03: Administrator Role Separation on Online Checkout Endpoints
- **Root Cause:** `/api/orders/checkout` checked authentication but lacked role discrimination, permitting administrator accounts to invoke customer online cart workflows.
- **Fix:** Enforced `current_user.role == 'customer'` on `/api/orders/checkout` (returning 403 Forbidden for administrators); extended `/api/orders/<id>` so administrators can inspect any order while customer users remain scoped to their own.

### RE-AUDIT-04: Concurrency & Audit Trail in Admin Stock Restocks
- **Root Cause:** `backend/routes/admin/purchases.py` directly mutated `product.stock_quantity += quantity` without row-level locking or audit logging.
- **Fix:** Stock restocks now route through `InventoryService.add_stock`, providing PostgreSQL/MySQL row-level serialization via `with_for_update()` and recording an immutable `ADD_STOCK` event in `ActivityLog`.

### RE-AUDIT-05: Customer Credit Settlement Audit Logging
- **Root Cause:** Settling customer store credit in `backend/routes/admin/customers.py` updated debt balances without logging the financial transaction.
- **Fix:** Integrated `_log_action('CLEAR_CUSTOMER_CREDIT', 'User', user_id, details=...)` to record admin identity, settled amount, customer username, and client IP address.

### RE-AUDIT-06: Dual HTTP Method Support for API Session Termination
- **Root Cause:** `/api/auth/logout` only allowed POST, causing failures when clients invoked teardown via GET requests.
- **Fix:** Updated `@api_bp.route('/auth/logout', methods=['GET', 'POST'])` to support clean session termination across all consumption modes.

---

## 4. Verification & Automated Test Results

A dedicated security test suite `tests/test_security_audit.py` (16 tests) was implemented and verified alongside the entire application test suite.

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-7.4.3, pluggy-1.6.0
rootdir: D:\mart\mart
plugins: flask-1.3.0
collected 44 items

tests/test_api.py ..........                                             [ 22%]
tests/test_cart_service.py ...                                           [ 29%]
tests/test_order_service.py ..                                           [ 34%]
tests/test_routes.py .....                                               [ 45%]
tests/test_security_audit.py ................                            [ 81%]
tests/test_system_integration.py ........                                [100%]

======================= 44 passed, 8 warnings in 7.70s ========================
```

### Complete Coverage of Security Tests (`tests/test_security_audit.py`):
1. `test_2fa_enforcement_on_login`: Confirms 2FA staging and blocks unverified sessions.
2. `test_payment_idor_and_bola_prevention`: Blocks unauthorized users from initiating payment sessions for other orders.
3. `test_payment_tampering_rejection`: Prevents unauthorized payment success callbacks and preserves pending order status.
4. `test_udhar_credit_restriction`: Rejects credit checkout when limits or verification criteria are not met.
5. `test_wholesale_data_leakage_redaction`: Verifies absence of `cost_price` and `supplier_name` in public JSON APIs.
6. `test_file_upload_rejection_and_uuid_naming`: Rejects polyglots and confirms safe UUID naming for images.
7. `test_csv_formula_injection_sanitization`: Confirms neutralization of spreadsheet formula injection vectors.
8. `test_security_headers_and_csp`: Verifies nosniff, SAMEORIGIN, frame-ancestors, and refined CSP rules.
9. `test_cors_domain_isolation`: Verifies rejection of untrusted third-party Vercel subdomains.
10. `test_rate_limiter_blocks_brute_force`: Verifies that rapid login attempts trigger HTTP 429 Too Many Requests.
11. `test_api_auth_decorator_content_negotiation`: Verifies 401/403 JSON responses on unauthorized API calls.
12. `test_cumulative_store_credit_boundary_enforcement`: Confirms rejection of orders that exceed cumulative ₹5,000 credit.
13. `test_admin_cannot_checkout_online_orders`: Confirms 403 Forbidden when admin attempts online customer cart checkout.
14. `test_admin_purchase_atomic_inventory_and_audit_log`: Verifies row-locked restock and `ActivityLog` emission.
15. `test_admin_clear_credit_audit_log`: Verifies credit settlement generates an immutable `ActivityLog` record.
16. `test_api_logout_both_methods`: Verifies both GET and POST session termination at `/api/auth/logout`.

---

## 5. Deployment & Production Hardening Checklist

For production deployment on Render, Docker, or AWS:

1. **Environment Variables:**
   - Ensure `FLASK_ENV=production` and `FLASK_DEBUG=0`.
   - Set a high-entropy `SECRET_KEY` (minimum 64 hex characters).
   - Set `SESSION_COOKIE_SECURE=true` to enforce cookies over HTTPS only.
   - Configure custom `ADMIN_PASSWORD` and `ADMIN_USERNAME`.
   - Set `STRIPE_SECRET_KEY` and `STRIPE_PUBLISHABLE_KEY`.
2. **Database:**
   - Set `DATABASE_URL` with SSL mode enabled (`sslmode=require`).
   - Set `SKIP_DB_CREATE=true` to enforce migrations via Flask-Migrate.
3. **Storage:**
   - Configure `AWS_BUCKET_NAME`, `AWS_ACCESS_KEY_ID`, and `AWS_SECRET_ACCESS_KEY` for off-server S3 media asset storage.
4. **Monitoring & Alerts:**
   - Configure a persistent Redis backend for Flask-Limiter (`RATELIMIT_STORAGE_URL=redis://...`).
   - Monitor 4xx/5xx spikes and rate-limit triggers.
