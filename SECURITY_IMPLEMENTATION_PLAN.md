# E-GROSSARY — SECURITY IMPLEMENTATION PLAN

## 1. Overview
This plan outlines the staged implementation of defensive security controls across all application tiers of the e Grossary system, moving from critical authentication/authorization repairs to defense-in-depth hardening and regression test suites.

---

## 2. Phase Breakdown

### Phase 1 — Critical Security Fixes
* **2FA Unified Enforcement:** Unify authentication handling across `/admin/login`, `/login`, and `/api/auth/login`. Ensure any user with `two_factor_enabled=True` is halted at staging and requires TOTP validation before any session is created.
* **BOLA/IDOR Elimination:** Add strict customer ownership verification (`order.user_id == current_user.id`) to `/create-checkout-session/<order_id>` and `/payment/success/<order_id>`.
* **Payment Tamper Defense:** Verify that Stripe checkout sessions match the order's primary key and total payable amount before updating status to 'Paid'. Disable arbitrary simulated payments in non-test/production environments.
* **Stored XSS Elimination:** Add an HTML entity escaping helper (`escapeHTML`) and escape all dynamic fields rendered via `innerHTML` in `admin.js`, `customer.js`, and `homepage.js`.
* **CORS Whitelist Restructuring:** Remove open wildcard Vercel regex (`^https:\/\/.*\.vercel\.app$`) and restrict allowed origins strictly to the production frontend domain and explicitly configured environments.

### Phase 2 — High-Risk Hardening
* **Wholesale Data Redaction:** Separate public product serialization from admin serialization. Ensure `cost_price`, `profit_margin`, `minimum_stock_alert`, and `supplier_name` are never leaked to public/customer clients.
* **Magic-Byte Image Upload Validation:** Verify uploaded files using Pillow image signature inspection (`Image.open`) to block disguised polyglots and executable scripts. Enforce secure UUID file naming.
* **API Rate Limiting:** Enforce strict Flask-Limiter policies on login (`5/min`), registration (`3/min`), TOTP verification (`5/min`), and checkout (`10/min`).
* **Store Credit (Udhar) Authorization Guard:** Guard `payment_method='UDHAR'` by enforcing credit balance ceilings and requiring verified customer status.
* **Password Reset Expiration:** Add 15-minute token expiration enforcement to password reset tokens.

### Phase 3 — Medium / Low Risk Hardening
* **CSV Formula Sanitization:** Escape spreadsheet formula injection characters (`=`, `+`, `-`, `@`, `\t`, `\r`) with leading single quotes (`'`).
* **Runtime Defect Repairs:**
  - Implement `OrderService.create_order_from_cart` in `backend/services/order_service.py` to restore `/api/orders/checkout`.
  - Fix missing `url_for` import in `backend/routes/admin/sales.py`.
  - Fix `order.items` relationship query bug in order detail endpoints.
* **Security Headers & CSP:** Enforce HSTS, remove `*` from `img-src` in Content-Security-Policy, and set nosniff headers on file upload delivery.
* **Safe Error Handling:** Catch and sanitize exceptions to prevent server stack traces or database errors from leaking into JSON API responses.

### Phase 4 — Automated Verification & Regression Protection
* Implement automated security test suite in `tests/test_security_audit.py`.
* Run entire pytest suite (`pytest`) to guarantee 100% test passing rate and zero functional regression.
* Generate final verification documentation in `SECURITY_FINAL_REPORT.md`.
