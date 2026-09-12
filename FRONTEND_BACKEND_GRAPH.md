# 🌐 Frontend & Backend Architecture & Connection Graph

> **Project:** e Grossary (E-Commerce & Retail ERP)  
> **Repository:** `d:/mart/mart`  
> **Tech Stack:** Vanilla JavaScript (ES6+), Bootstrap 5, Python Flask, Flask Blueprints, SQLAlchemy ORM, PostgreSQL / SQLite, Vercel Edge CDN, Render Cloud WSGI.

---

## 📑 Table of Contents
1. [High-Level System Architecture](#1-high-level-system-architecture)
2. [Network, Gateway & Proxy Flow](#2-network-gateway--proxy-flow)
3. [Client-Side UI to Backend Blueprint Mapping](#3-client-side-ui-to-backend-blueprint-mapping)
4. [End-to-End Sequence Diagrams](#4-end-to-end-sequence-diagrams)
   - [A. Product Catalog Browsing & Search Flow](#a-product-catalog-browsing--search-flow)
   - [B. Reactive Cart Synchronization Flow](#b-reactive-cart-synchronization-flow)
   - [C. User Authentication Flow](#c-user-authentication-flow)
   - [D. Checkout & Order Fulfillment Pipeline](#d-checkout--order-fulfillment-pipeline)
   - [E. Admin ERP Dashboard & POS Terminal Flow](#e-admin-erp-dashboard--pos-terminal-flow)
5. [Complete API & Route Contract Reference](#5-complete-api--route-contract-reference)
6. [Deployment Topology & Dual-Mode Operation](#6-deployment-topology--dual-mode-operation)
7. [Database Entity Relationship & Data Sync](#7-database-entity-relationship--data-sync)
8. [Summary of Connection Mechanisms](#8-summary-of-connection-mechanisms)

---

## 1. High-Level System Architecture

The application operates in a **decoupled hybrid architecture** where the client presentation layer is hosted on Vercel's global Edge CDN, while the Python Flask application and relational database are hosted on Render Cloud.

```mermaid
graph TB
    %% ================= CLIENT LAYER =================
    subgraph ClientLayer["🖥️ Client Tier (Browser)"]
        User["👤 End Users / Shoppers"]
        AdminUser["👨‍💼 Store Managers / Admin"]

        subgraph WebPages["HTML5 Single Page Applications"]
            IndexPage["index.html<br/>(Storefront Homepage)"]
            CustomerPage["customer.html<br/>(Customer Super-App)"]
            AdminPage["admin.html<br/>(Admin Management ERP)"]
        end

        subgraph ClientEngines["JavaScript Engines & State"]
            HomepageJS["homepage.js<br/>(Catalog, Cart Drawer, Search)"]
            CustomerJS["customer.js<br/>(Shop, Orders, Tracking, Profile)"]
            AdminJS["admin.js<br/>(POS, Metrics, Inventory CRUD)"]
            ThemeJS["theme.js<br/>(Theme & Local Storage)"]
        end
    end

    %% ================= GATEWAY LAYER =================
    subgraph EdgeLayer["⚡ Vercel Edge & Reverse Proxy"]
        VercelCDN["Vercel Global CDN<br/>(Static Assets: HTML, CSS, JS, Images)"]
        VercelRewrite["Vercel Rewrites Engine (vercel.json)<br/>/api/:path* ➔ Render Backend<br/>/static/uploads/:path* ➔ Uploads Storage"]
    end

    %% ================= BACKEND LAYER =================
    subgraph BackendLayer["🐍 Flask Backend Server (Render / Gunicorn)"]
        WSGI["WSGI Gateway (wsgi.py / Gunicorn)"]
        
        subgraph CoreMiddleware["Core Security & Request Pipeline"]
            CORSHandler["Flask-CORS<br/>(Credentials: true, Allowed Origins)"]
            CSRFProtection["Flask-WTF CSRF<br/>(Exempt on /api/*, Enforced on Forms)"]
            RateLimiter["Flask-Limiter<br/>(DDoS & Brute-force Throttling)"]
            AuthSession["Flask-Login<br/>(Session Cookie: SameSite=None, Secure)"]
        end

        subgraph Blueprints["Modular Flask Blueprints"]
            API_BP["api_bp (/api/*)<br/>Decoupled JSON REST API"]
            AUTH_BP["auth_bp (/auth/*)<br/>Session Authentication"]
            ADMIN_BP["admin_bp (/admin/*)<br/>ERP Dashboard & Management"]
            CUSTOMER_BP["customer_bp (/*)<br/>Customer Portal & Template Routes"]
            SECURITY_BP["security_bp (/security/*)<br/>2FA, Passwords & Audit"]
        end

        subgraph Services["Domain Service Layer"]
            CartSvc["CartService<br/>(DB Cart & Guest Session Cart)"]
            OrderSvc["OrderService<br/>(Order Creation, Stock Deduct)"]
            ExportSvc["ExportService<br/>(PDF & CSV ReportLab Generation)"]
        end
    end

    %% ================= PERSISTENCE LAYER =================
    subgraph DataLayer["💾 Persistence & External Services"]
        SQLAlchemyORM["SQLAlchemy ORM Engine"]
        Database[("PostgreSQL / SQLite Database<br/>(Users, Products, Orders, Sales)")]
        LocalStorage["Client LocalStorage<br/>(jg_cart, jg_auth_user, jg_wishlist)"]
        MailService["SMTP Mail Server<br/>(Order Confirmations, 2FA, Resets)"]
        MediaStorage["Uploads Directory<br/>(/static/uploads/* Product Images)"]
    end

    %% Wire connections
    User --> IndexPage
    User --> CustomerPage
    AdminUser --> AdminPage

    IndexPage --- HomepageJS
    CustomerPage --- CustomerJS
    AdminPage --- AdminJS
    IndexPage --- ThemeJS

    HomepageJS -.->|Cache & Fallback| LocalStorage
    CustomerJS -.->|Cache & Fallback| LocalStorage
    AdminJS -.->|Cache & Fallback| LocalStorage

    WebPages -->|1. Static Asset Requests| VercelCDN
    HomepageJS -->|2. /api/* Requests| VercelRewrite
    CustomerJS -->|2. /api/* Requests| VercelRewrite
    AdminJS -->|2. /api/* Requests| VercelRewrite

    VercelRewrite -->|Proxy Forward via HTTPS| WSGI
    WSGI --> CoreMiddleware
    CoreMiddleware --> Blueprints

    API_BP --> Services
    ADMIN_BP --> Services
    CUSTOMER_BP --> Services

    Services --> SQLAlchemyORM
    SQLAlchemyORM --> Database
    CUSTOMER_BP -.-> MailService
    ADMIN_BP -.-> ExportSvc
    VercelRewrite -->|Fetch Media| MediaStorage
```

---

## 2. Network, Gateway & Proxy Flow

The connection between the client browser and the backend server uses **transparent reverse-proxying** to avoid cross-origin friction while supporting direct cross-origin access during development.

```mermaid
flowchart LR
    subgraph Client["Browser (https://glossary-mart.vercel.app)"]
        direction TB
        FetchReq["fetch('/api/products')<br/>fetch('/api/cart/add')<br/>fetch('/api/auth/login')"]
    end

    subgraph VercelProxy["Vercel Edge Proxy (vercel.json)"]
        direction TB
        RewriteRule["Rewrites Rule Match:<br/>source: /api/:path*<br/>destination: https://glossary-mart.onrender.com/api/:path*"]
        HeaderEnforce["Security Headers Attached:<br/>X-Content-Type-Options: nosniff<br/>X-Frame-Options: SAMEORIGIN<br/>Referrer-Policy: strict-origin"]
    end

    subgraph RenderApp["Render Backend (https://glossary-mart.onrender.com)"]
        direction TB
        CORSEval{"CORS & Origin Check"}
        CSRFEval{"CSRF Exemption Check"}
        FlaskRouter["Flask Endpoint Handler"]
    end

    FetchReq -->|Same-origin URL call| RewriteRule
    RewriteRule --> HeaderEnforce
    HeaderEnforce -->|HTTPS Forwarding| CORSEval

    CORSEval -->|Allowed: Vercel / Localhost| CSRFEval
    CSRFEval -->|/api/* Exempted| FlaskRouter
    FlaskRouter -->|JSON Response Payload| Client
```

---

## 3. Client-Side UI to Backend Blueprint Mapping

This graph maps the frontend user interfaces and scripts to their corresponding Flask routes, service classes, and database models.

```mermaid
graph LR
    subgraph FrontendComponents["Frontend UI & Scripts"]
        subgraph IndexUI["Storefront (index.html + homepage.js)"]
            UI_Catalog["Product Catalog Grid"]
            UI_CartDrawer["Reactive Cart Drawer"]
            UI_AuthModal["Login & Register Modal"]
            UI_Search["Instant Search Bar"]
        end

        subgraph CustomerUI["Customer Portal (customer.html + customer.js)"]
            UI_Shop["Shop & Filter View"]
            UI_Checkout["Multi-Step Checkout"]
            UI_OrderTrack["Live Order Tracking"]
            UI_Profile["User Profile & Addresses"]
        end

        subgraph AdminUI["Admin ERP (admin.html + admin.js)"]
            UI_Dashboard["Analytics & Chart.js"]
            UI_Inventory["Product Catalog Management"]
            UI_POS["POS Terminal & Cash Billing"]
            UI_OrderMgt["Order Pipeline & Status"]
        end
    end

    subgraph FlaskBlueprints["Backend Flask Blueprints"]
        API_Products["/api/products<br/>(api_bp.products)"]
        API_Cart["/api/cart/*<br/>(api_bp.cart)"]
        API_Auth["/api/auth/*<br/>(api_bp.auth)"]
        API_Orders["/api/orders/*<br/>(api_bp.orders)"]
        ADMIN_Routes["/admin/*<br/>(admin_bp.*)"]
    end

    subgraph DatabaseEntities["SQLAlchemy Models & DB"]
        Model_Product[("Product & Category")]
        Model_Cart[("Cart & CartItem")]
        Model_User[("User & Session")]
        Model_Order[("Order & OrderItem")]
        Model_Sale[("Sale & Inventory Log")]
    end

    %% Connections for Index
    UI_Catalog -->|GET| API_Products
    UI_Search -->|GET ?search=| API_Products
    UI_CartDrawer -->|GET, POST, PUT, DELETE| API_Cart
    UI_AuthModal -->|POST /login, /register| API_Auth

    %% Connections for Customer
    UI_Shop -->|GET| API_Products
    UI_Checkout -->|POST /orders/checkout| API_Orders
    UI_OrderTrack -->|GET /orders/<id>| API_Orders
    UI_Profile -->|GET /auth/me| API_Auth

    %% Connections for Admin
    UI_Dashboard -->|GET /analytics, /products| ADMIN_Routes
    UI_Inventory -->|POST, PUT, DELETE| ADMIN_Routes
    UI_POS -->|POST /admin/pos/checkout| ADMIN_Routes
    UI_OrderMgt -->|POST /admin/orders/<id>/status| ADMIN_Routes

    %% Connections to Models
    API_Products --> Model_Product
    API_Cart --> Model_Cart
    API_Auth --> Model_User
    API_Orders --> Model_Order
    ADMIN_Routes --> Model_Sale
    ADMIN_Routes --> Model_Product
    ADMIN_Routes --> Model_Order
```

---

## 4. End-to-End Sequence Diagrams

### A. Product Catalog Browsing & Search Flow
How `homepage.js` and `customer.js` fetch active inventory with category filtering, search queries, and fallback to local state.

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 Customer Browser
    participant JS as 📜 homepage.js / customer.js
    participant Vercel as ⚡ Vercel Edge Proxy
    participant Flask as 🐍 Flask (/api/products)
    participant DB as 💾 Database (SQLAlchemy)

    User->>JS: Enters Storefront / Types Search Term
    JS->>Vercel: fetch('/api/products?search=atta&category=1&page=1')
    Vercel->>Flask: Proxy pass to Render: GET /api/products
    Flask->>Flask: Validate query parameters & sanitize input
    Flask->>DB: Product.query.filter_by(is_active=True).filter(ilike(...))
    DB-->>Flask: List of Product records
    Flask-->>Vercel: JSON Response: { success: true, total: 12, products: [...] }
    Vercel-->>JS: Forward JSON payload
    alt Live API Successful
        JS->>JS: Map products into catalog state & render DOM
    else API Down / Cold Start Failure
        JS->>JS: Catch network error & hydrate from local fallback catalog
    end
    JS-->>User: Display Product Grid with prices, discounts & stock badges
```

---

### B. Reactive Cart Synchronization Flow
How adding an item updates the UI instantly, stores state in `localStorage`, and asynchronously syncs with the Flask session/database.

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 Customer
    participant UI as 🛒 Cart Drawer (DOM)
    participant Storage as 💾 localStorage ('jg_cart')
    participant JS as 📜 homepage.js (Cart Engine)
    participant Flask as 🐍 Flask (/api/cart/add)
    participant CartSvc as ⚙️ CartService
    participant DB as 💾 Database / Session

    User->>UI: Clicks "+ Add to Cart" on Product Card
    UI->>JS: addToCart(product, quantity=1)
    JS->>JS: Update in-memory cart array & recalculate totals
    JS->>Storage: Persist updated cart array to 'jg_cart'
    JS->>UI: Update Cart Badge Count, Drawer items, and Subtotal
    JS-->>User: Show Toast: "Added Aashirvaad Atta to cart!"

    opt Asynchronous Background Sync
        JS->>Flask: fetch('/api/cart/add', { method: 'POST', body: { product_id: 1, quantity: 1 } })
        Flask->>CartSvc: CartService.add_item(product_id=1, quantity=1)
        alt Authenticated Customer
            CartSvc->>DB: Upsert CartItem in Database
        else Guest User
            CartSvc->>DB: Store item in Flask session['guest_cart']
        end
        CartSvc-->>Flask: (success=True, message="Item added to cart")
        Flask-->>JS: HTTP 200 { success: true }
    end
```

---

### C. User Authentication Flow
Customer or Admin login flow supporting decoupled JSON credentials and session cookie persistence.

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 Customer / 👨‍💼 Admin
    participant Modal as 🪟 Auth Modal Form
    participant JS as 📜 homepage.js (Auth Module)
    participant Flask as 🐍 Flask (/api/auth/login)
    participant AuthMgr as 🔐 Flask-Login & Werkzeug
    participant DB as 💾 Database (User Table)

    User->>Modal: Inputs Email/Username and Password
    Modal->>JS: handleCustomerLogin(event)
    JS->>JS: Display spinner: "Authenticating..."
    JS->>Flask: POST /api/auth/login { username, password, remember: true }
    Flask->>DB: User.query.filter(User.email == input).first()
    DB-->>Flask: User record with password_hash
    Flask->>AuthMgr: check_password_hash(user.password_hash, password)
    
    alt Credentials Valid
        AuthMgr->>Flask: Success (User verified)
        Flask->>Flask: login_user(user, remember=True)
        Flask-->>JS: HTTP 200 { success: true, user: { id: 1, name: "Admin", role: "admin" } }
        JS->>JS: Save sessionUser to localStorage ('jg_auth_user')
        JS-->>User: Show Toast: "Welcome back, Admin!"
        alt Role is Admin
            JS->>User: Redirect to 'admin.html#dashboard'
        else Role is Customer
            JS->>User: Redirect to 'customer.html#shop'
        end
    else Invalid Credentials
        Flask-->>JS: HTTP 401 { success: false, message: "Invalid username or password" }
        JS->>Modal: Display error banner: "Invalid credentials"
    end
```

---

### D. Checkout & Order Fulfillment Pipeline
Full end-to-end checkout flow from customer confirmation to backend transaction and inventory reduction.

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 Customer
    participant CheckoutUI as 💳 customer.html (Step 3 Checkout)
    participant CustomerJS as 📜 customer.js
    participant Flask as 🐍 Flask (/api/orders/checkout)
    participant OrderSvc as 📦 OrderService
    participant DB as 💾 Database
    participant Mail as ✉️ Flask-Mail (SMTP)

    User->>CheckoutUI: Selects Payment Method (COD / UPI / Card) & Confirms Order
    CheckoutUI->>CustomerJS: submitCheckoutOrder()
    CustomerJS->>Flask: POST /api/orders/checkout { shipping_address, payment_method }
    Flask->>OrderSvc: create_order_from_cart(user_id, shipping_address, payment_method)
    
    critical Database Transaction
        OrderSvc->>DB: Fetch active Cart & CartItems for user
        OrderSvc->>DB: Create new Order record (Status: 'Pending', Payment: 'Unpaid')
        loop For each cart item
            OrderSvc->>DB: Insert OrderItem record
            OrderSvc->>DB: Deduct Product.stock_quantity
            OrderSvc->>DB: Insert Inventory StockLog record
        end
        OrderSvc->>DB: Clear user's Cart & CartItems
        OrderSvc->>DB: db.session.commit()
    end

    opt Email Notification
        OrderSvc->>Mail: Send order confirmation email to Customer
    end

    OrderSvc-->>Flask: (order_object, message="Order placed successfully")
    Flask-->>CustomerJS: HTTP 200 { success: true, order: { id: 1042, total: 649, status: "Pending" } }
    CustomerJS->>CustomerJS: Clear local cart from 'jg_cart'
    CustomerJS->>CheckoutUI: Navigate to #order-confirmation view
    CheckoutUI-->>User: Display Confirmed Order ID #1042 & Estimated Delivery Time
```

---

### E. Admin ERP Dashboard & POS Terminal Flow
Point-of-Sale (POS) counter transaction and real-time Chart.js dashboard metrics synchronization.

```mermaid
sequenceDiagram
    autonumber
    actor Admin as 👨‍💼 Cashier / Store Admin
    participant AdminUI as 🖥️ admin.html (POS & Dashboard)
    participant AdminJS as 📜 admin.js
    participant AdminRoutes as 🐍 Flask (/admin/pos, /admin/dashboard)
    participant DB as 💾 Database
    participant ReportLab as 📄 ReportLab Service

    Admin->>AdminUI: Opens POS view, searches item, adds to cash cart
    AdminUI->>AdminJS: addPosItem(productId, qty)
    AdminJS->>AdminJS: Calculate subtotal, GST, and change due
    Admin->>AdminUI: Clicks "Complete Sale & Print Invoice"
    AdminUI->>AdminRoutes: POST /admin/pos/checkout { items: [...], customer_name, payment: 'cash' }
    
    AdminRoutes->>DB: Record Sale & SaleItems
    AdminRoutes->>DB: Decrement Product Stock
    AdminRoutes->>ReportLab: Generate printable PDF receipt
    ReportLab-->>AdminRoutes: In-memory PDF bytes buffer
    DB-->>AdminRoutes: Commit transaction
    AdminRoutes-->>AdminJS: HTTP 200 { success: true, sale_id: 88, invoice_url: "/admin/sales/88/invoice" }
    
    AdminJS->>AdminJS: Trigger auto-print or PDF download modal
    AdminJS->>AdminRoutes: GET /admin/dashboard (or /admin/api/analytics)
    AdminRoutes->>DB: Aggregate total sales, revenue, low stock count
    DB-->>AdminRoutes: Sales analytics JSON
    AdminRoutes-->>AdminJS: Return revenue figures & 7-day trend
    AdminJS->>AdminUI: Re-render Chart.js Revenue Trend Chart & Low-Stock Alerts
```

---

## 5. Complete API & Route Contract Reference

| Frontend Feature | Client Caller | HTTP | Backend Route | Blueprint / Handler | Response Type | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Catalog Feed** | `homepage.js` / `customer.js` | `GET` | `/api/products` | `api_bp.get_products` | `JSON` | Paginated product list with search, category & price filters |
| **Product Detail** | `customer.js` | `GET` | `/api/products/<id>` | `api_bp.get_product_detail` | `JSON` | Full details, stock level, ratings, and customer reviews |
| **View Cart** | `homepage.js` / `customer.js` | `GET` | `/api/cart` | `api_bp.get_cart` | `JSON` | Current items, quantities, subtotal & free shipping progress |
| **Add to Cart** | `homepage.js` / `customer.js` | `POST` | `/api/cart/add` | `api_bp.add_to_cart` | `JSON` | Add product to session or DB cart |
| **Update Cart** | `customer.js` | `PUT` | `/api/cart/update` | `api_bp.update_cart` | `JSON` | Update quantity of cart line item |
| **Remove Item** | `homepage.js` / `customer.js` | `DELETE`| `/api/cart/remove` | `api_bp.remove_from_cart` | `JSON` | Delete single item from cart |
| **Clear Cart** | `customer.js` | `DELETE`| `/api/cart/clear` | `api_bp.clear_cart` | `JSON` | Empty entire cart |
| **User Profile** | `homepage.js` / `customer.js` | `GET` | `/api/auth/me` | `api_bp.get_current_user` | `JSON` | Current authenticated session info |
| **User Login** | `homepage.js` (Auth Modal) | `POST` | `/api/auth/login` | `api_bp.api_login` | `JSON` | Authenticate customer/admin, issue session cookie |
| **Register** | `homepage.js` (Auth Modal) | `POST` | `/api/auth/register` | `api_bp.api_register` | `JSON` | Create new customer user account |
| **Logout** | Header UI | `POST` | `/api/auth/logout` | `api_bp.api_logout` | `JSON` | Destroy session & invalidate cookies |
| **List Orders** | `customer.js` (My Orders) | `GET` | `/api/orders` | `api_bp.get_orders` | `JSON` | Fetch past orders for logged in user |
| **Order Detail** | `customer.js` (Tracking) | `GET` | `/api/orders/<id>` | `api_bp.get_order_detail` | `JSON` | Line items and status progression of specific order |
| **Checkout** | `customer.js` (Checkout) | `POST` | `/api/orders/checkout` | `api_bp.api_checkout` | `JSON` | Turn cart into placed order, reduce stock |
| **Health Check** | Ping Monitor | `GET` | `/api/health` | `api_bp.api_health` | `JSON` | Backend status verification |
| **POS Billing** | `admin.js` (POS View) | `POST` | `/admin/pos/checkout` | `admin_bp.pos_checkout` | `JSON / PDF` | Record in-store sale & deduct inventory |
| **PDF Export** | `admin.js` (Reports) | `GET` | `/admin/sales/export/pdf` | `admin_bp.export_sales_pdf` | `Binary PDF` | ReportLab-generated sales statement |
| **Media Images** | `img` tags in DOM | `GET` | `/static/uploads/<filename>` | `app.uploaded_file` | `Image/JPEG/PNG`| Uploaded product image files |

---

## 6. Deployment Topology & Dual-Mode Operation

e Grossary is architected to operate smoothly in two distinct deployment modes without requiring code refactoring:

```mermaid
graph TD
    subgraph Mode1["Mode 1: Decoupled Cloud Production (Vercel + Render)"]
        BrowserProd["User Browser"]
        VercelCDNProd["Vercel Edge Network (glossary-mart.vercel.app)<br/>• index.html, customer.html, admin.html<br/>• Static CSS / JS assets"]
        RenderServerProd["Render Cloud Service (glossary-mart.onrender.com)<br/>• Gunicorn WSGI Python Flask Server<br/>• REST API Endpoints (/api/*)"]
        PostgresProd[("Render Managed PostgreSQL")]

        BrowserProd -->|HTTPS| VercelCDNProd
        BrowserProd -->|Rewrites Proxy: /api/*| RenderServerProd
        RenderServerProd --> PostgresProd
    end

    subgraph Mode2["Mode 2: Monolithic Local / Full-Stack (Flask Direct)"]
        BrowserLocal["Local Browser (localhost:5000)"]
        FlaskMonolith["Flask Application Server<br/>• Serves frontend/ as template & static folder<br/>• Serves API endpoints directly"]
        SQLiteLocal[("Local SQLite Database (store.db)")]

        BrowserLocal --> FlaskMonolith
        FlaskMonolith --> SQLiteLocal
    end
```

### Client-Side Graceful Degradation:
1. **Live Synchronization First**: On page load, `homepage.js`, `customer.js`, and `admin.js` initiate asynchronous `fetch('/api/products')` and `fetch('/api/cart')` calls.
2. **Cold-Start Protection**: If Render's free web service is spinning up from idle (cold-start delay ~30-50s) or offline, the JavaScript engines catch the promise rejection and smoothly fall back to client-side catalogs and `localStorage` caches.
3. **Session Rehydration**: Logged-in credentials are saved both in Flask's secure HTTP-only cookies and in `localStorage.setItem('jg_auth_user')`, ensuring UI state continuity even across page switches.

---

## 7. Database Entity Relationship & Data Sync

This diagram shows how backend models in `database/models/` map directly to the frontend's reactive state objects.

```mermaid
erDiagram
    USER ||--o{ ORDER : "places"
    USER ||--o{ CART_ITEM : "stores in DB"
    USER ||--o{ REVIEW : "submits"
    CATEGORY ||--o{ PRODUCT : "classifies"
    PRODUCT ||--o{ ORDER_ITEM : "ordered in"
    PRODUCT ||--o{ CART_ITEM : "added to"
    PRODUCT ||--o{ SALE_ITEM : "sold via POS"
    ORDER ||--|{ ORDER_ITEM : "contains"
    SALE ||--|{ SALE_ITEM : "records"

    USER {
        int id PK
        string username
        string email
        string password_hash
        string role "admin | customer"
        string full_name
        string phone
        text address
    }

    PRODUCT {
        int id PK
        string name
        int category_id FK
        float cost_price
        float selling_price
        int stock_quantity
        string image_path
        boolean is_active
    }

    CART_ITEM {
        int id PK
        int user_id FK
        int product_id FK
        int quantity
        datetime added_at
    }

    ORDER {
        int id PK
        int user_id FK
        float total_amount
        string order_status "Pending | Processing | Shipped | Delivered"
        string payment_method "COD | UPI | CARD"
        string payment_status "Unpaid | Paid"
        text shipping_address
        datetime created_at
    }

    ORDER_ITEM {
        int id PK
        int order_id FK
        int product_id FK
        int quantity
        float unit_price
        float subtotal
    }

    SALE {
        int id PK
        float total_amount
        string payment_method "Cash | Online"
        datetime sale_date
    }

    SALE_ITEM {
        int id PK
        int sale_id FK
        int product_id FK
        int quantity
        float unit_price
        float subtotal
    }
```

---

## 8. Summary of Connection Mechanisms

| Channel / Mechanism | Direction | Protocol / Transport | Security & Configuration |
| :--- | :--- | :--- | :--- |
| **Vercel Rewrites** | Client ➔ Render Backend | HTTPS Reverse Proxy | Configured in `vercel.json`; transparently bridges `/api/*` to Render |
| **Direct Fetch (CORS)** | Client ➔ Backend | HTTP/2 or HTTPS Fetch API | Configured with `flask_cors.CORS`, `supports_credentials=True`, origins whitelist |
| **Session Tracking** | Backend ⇄ Client | Secure HTTP-only Cookie | `SESSION_COOKIE_SAMESITE='None'`, `SESSION_COOKIE_SECURE=True` in production |
| **Local Client Storage** | JS ⇄ Browser Storage | Web Storage API | Stores cart (`jg_cart`), auth (`jg_auth_user`), theme (`jg_theme`) for zero-latency UI |
| **Static File Uploads** | Backend ➔ Client | HTTPS Static File Delivery | Endpoint `/static/uploads/<filename>` routed to physical disk storage folder |
| **Invoice / Data Export** | Backend ➔ Client | Streamed Binary / Blob | ReportLab PDF stream and CSV formatted downloads via `flask.send_file` |
