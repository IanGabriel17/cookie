# Bakery Sales and Inventory System Diagram Package

This document is the generated visual documentation package for the Bakery Sales and Inventory System. It uses the project documentation, Django models, URL routes, services, and database schema as the factual basis for the diagrams.

## Unified Visual Legend

| Element Type | Color | Meaning |
|---|---:|---|
| External users / actors | Orange | Human roles and outside users |
| Processes / modules | Blue | Application workflows and system services |
| Data stores / databases | Green | Persistent tables, files, and reports |
| Decisions | Yellow | Branching rules and validations |
| Relationships / connectors | Gray | Data movement, control flow, and dependencies |

```mermaid
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "Inter, Segoe UI, Arial", "primaryTextColor": "#172033", "lineColor": "#6b7280", "background": "#ffffff"}}}%%
flowchart LR
  actor([External Users / Actors])
  process[Processes / Modules]
  store[(Data Stores)]
  decision{Decision Nodes}
  actor --> process --> decision --> store

  classDef actor fill:#fff3e0,stroke:#f97316,color:#7c2d12,stroke-width:2px;
  classDef process fill:#eaf3ff,stroke:#2563eb,color:#1e3a8a,stroke-width:2px;
  classDef store fill:#eaf8ef,stroke:#16a34a,color:#14532d,stroke-width:2px;
  classDef decision fill:#fff7cc,stroke:#eab308,color:#713f12,stroke-width:2px;
  classDef connector stroke:#6b7280,color:#374151;
  class actor actor;
  class process process;
  class store store;
  class decision decision;
```

## Extracted System Elements

| Category | Extracted Items |
|---|---|
| User roles | Admin, Cashier, Inventory Staff, Customer |
| Main modules | Authentication, Dashboard, POS/Sales, Inventory, Catalog, Orders, Reports, Audit Logs, Employee Management, Backup |
| Core entities | User, Group, EmployeeSecurity, Category, Supplier, Product, ProductionBatch, BatchAllocation, Order, Sale, SaleItem, VoidedSaleItem, InventoryLog, ActivityLog, LoginHistory, Note |
| Main workflows | Login, forced password change, product/category/supplier management, stock restock/adjustment, FIFO sales, sale void, custom order tracking, report export, audit review |
| Outputs | Receipts, PDF receipts, sales CSV/XLSX/PDF reports, dashboard metrics, inventory movement logs, activity logs, login history, SQLite backup in local development |
| Key business rules | Role-based access, positive quantities, non-negative money/stock, pickup date not before order date, FIFO batch allocation, void reason required, admin-only void, append-only logs, archived products unavailable for orders/sales, last active admin protected |

## 1. Conceptual Framework

```mermaid
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "Inter, Segoe UI, Arial", "lineColor": "#6b7280", "background": "#ffffff"}}}%%
flowchart LR
  subgraph I[Input Layer]
    I1([User credentials])
    I2([Product and supplier data])
    I3([POS cart, barcode, payment, discount, tax])
    I4([Stock restock, adjustment, production batch])
    I5([Customer order details])
  end

  subgraph P[Process Layer]
    P1[Authenticate and authorize user]
    P2[Manage catalog and inventory]
    P3[Process sale transaction]
    P4[Allocate FIFO batch stock]
    P5[Generate reports and audit records]
  end

  subgraph O[Output Layer]
    O1[(Updated database records)]
    O2[(Inventory and activity logs)]
    O3[(Receipts and report exports)]
    O4[(Dashboard analytics)]
    O5[(Low-stock and status visibility)]
  end

  I1 --> P1
  I2 --> P2
  I3 --> P3
  I4 --> P2
  I5 --> P2
  P1 --> P2
  P2 --> P3
  P3 --> P4
  P2 --> P5
  P3 --> P5
  P4 --> O1
  P5 --> O2
  P5 --> O3
  P5 --> O4
  P2 --> O5

  classDef actor fill:#fff3e0,stroke:#f97316,color:#7c2d12,stroke-width:2px;
  classDef process fill:#eaf3ff,stroke:#2563eb,color:#1e3a8a,stroke-width:2px;
  classDef store fill:#eaf8ef,stroke:#16a34a,color:#14532d,stroke-width:2px;
  class I1,I2,I3,I4,I5 actor;
  class P1,P2,P3,P4,P5 process;
  class O1,O2,O3,O4,O5 store;
```

## 2. System Flowchart

```mermaid
%%{init: {"theme": "base", "flowchart": {"curve": "basis"}, "themeVariables": {"fontFamily": "Inter, Segoe UI, Arial", "lineColor": "#6b7280", "background": "#ffffff"}}}%%
flowchart TD
  A([Start])
  B[Open login page]
  C[Submit username and password]
  D{Credentials valid?}
  E[(Record failed login)]
  F[Create session and record login]
  G{Temporary password active?}
  H[Force password change]
  I{Password valid?}
  J[Update password security status]
  K[Show role-aware dashboard]
  L{Select workflow}
  M[POS sale workflow]
  N[Catalog and inventory workflow]
  O[Order management workflow]
  P[Reports and backup workflow]
  Q[Audit review workflow]
  R[(Persist changes and logs)]
  S([Logout / End])

  A --> B --> C --> D
  D -- No --> E --> B
  D -- Yes --> F --> G
  G -- Yes --> H --> I
  I -- No --> H
  I -- Yes --> J --> K
  G -- No --> K
  K --> L
  L --> M --> R
  L --> N --> R
  L --> O --> R
  L --> P --> R
  L --> Q --> R
  R --> K
  K --> S

  classDef process fill:#eaf3ff,stroke:#2563eb,color:#1e3a8a,stroke-width:2px;
  classDef store fill:#eaf8ef,stroke:#16a34a,color:#14532d,stroke-width:2px;
  classDef decision fill:#fff7cc,stroke:#eab308,color:#713f12,stroke-width:2px;
  classDef actor fill:#fff3e0,stroke:#f97316,color:#7c2d12,stroke-width:2px;
  class A,S actor;
  class B,C,F,H,J,K,L,M,N,O,P,Q process;
  class E,R store;
  class D,G,I decision;
```

## 3. Data Flow Diagram Level 0

```mermaid
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "Inter, Segoe UI, Arial", "lineColor": "#6b7280", "background": "#ffffff"}}}%%
flowchart LR
  Admin([Admin])
  Cashier([Cashier])
  Inv([Inventory Staff])
  Customer([Customer])

  System[0. Bakery Sales and Inventory System]

  DB[(Application Database)]
  Media[(Product Image Storage)]
  Reports[(Report / Receipt Files)]
  Email[[Email Service]]

  Admin -->|employee, catalog, reports, void approval| System
  Cashier -->|POS sales and receipts| System
  Inv -->|stock, products, batches, reports| System
  Customer -->|order and payment details| System

  System -->|dashboard, receipt, order status| Admin
  System -->|receipt and transaction status| Cashier
  System -->|inventory status and alerts| Inv
  System -->|receipt or pickup details| Customer

  System <--> DB
  System --> Media
  System --> Reports
  System -->|password reset email| Email

  classDef actor fill:#fff3e0,stroke:#f97316,color:#7c2d12,stroke-width:2px;
  classDef process fill:#eaf3ff,stroke:#2563eb,color:#1e3a8a,stroke-width:2px;
  classDef store fill:#eaf8ef,stroke:#16a34a,color:#14532d,stroke-width:2px;
  class Admin,Cashier,Inv,Customer actor;
  class System process;
  class DB,Media,Reports,Email store;
```

## 4. Data Flow Diagram Level 1

```mermaid
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "Inter, Segoe UI, Arial", "lineColor": "#6b7280", "background": "#ffffff"}}}%%
flowchart TB
  subgraph Actors[External Entities]
    Admin([Admin])
    Cashier([Cashier])
    Inv([Inventory Staff])
    Customer([Customer])
  end

  subgraph Processes[Expanded System Processes]
    P1[1.0 Authentication and Role Control]
    P2[2.0 Catalog Management]
    P3[3.0 Inventory and Batch Control]
    P4[4.0 POS Sale Processing]
    P5[5.0 Order Management]
    P6[6.0 Reporting and Backup]
    P7[7.0 Audit and Login Monitoring]
  end

  subgraph Stores[Data Stores]
    D1[(Users, Groups, EmployeeSecurity)]
    D2[(Category, Supplier, Product)]
    D3[(ProductionBatch, BatchAllocation, InventoryLog)]
    D4[(Sale, SaleItem, VoidedSaleItem)]
    D5[(Order)]
    D6[(ActivityLog, LoginHistory)]
    D7[(Report Exports and Backup File)]
  end

  Admin --> P1
  Cashier --> P1
  Inv --> P1
  P1 <--> D1
  P1 --> P7

  Admin --> P2
  Inv --> P2
  P2 <--> D2
  P2 --> P7

  Admin --> P3
  Inv --> P3
  P3 <--> D2
  P3 <--> D3
  P3 --> P7

  Cashier --> P4
  Customer --> P4
  P4 --> D4
  P4 --> D3
  P4 --> D2
  P4 --> P7

  Admin --> P5
  Inv --> P5
  Customer --> P5
  P5 <--> D5
  P5 --> D2
  P5 --> P7

  Admin --> P6
  Inv --> P6
  P6 --> D2
  P6 --> D3
  P6 --> D4
  P6 --> D7
  P6 --> P7

  Admin --> P7
  P7 --> D6

  classDef actor fill:#fff3e0,stroke:#f97316,color:#7c2d12,stroke-width:2px;
  classDef process fill:#eaf3ff,stroke:#2563eb,color:#1e3a8a,stroke-width:2px;
  classDef store fill:#eaf8ef,stroke:#16a34a,color:#14532d,stroke-width:2px;
  class Admin,Cashier,Inv,Customer actor;
  class P1,P2,P3,P4,P5,P6,P7 process;
  class D1,D2,D3,D4,D5,D6,D7 store;
```

## 5. Use Case Diagram

```mermaid
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "Inter, Segoe UI, Arial", "lineColor": "#6b7280", "background": "#ffffff"}}}%%
flowchart LR
  Admin([Admin])
  Cashier([Cashier])
  Inv([Inventory Staff])

  subgraph Boundary[Bakery Sales and Inventory System]
    UC1((Authenticate))
    UC2((View dashboard))
    UC3((Manage employees))
    UC4((Manage categories, products, suppliers))
    UC5((Restock and adjust inventory))
    UC6((Manage production batches))
    UC7((Process POS sale))
    UC8((Print / export receipt))
    UC9((Void sale with reason))
    UC10((Manage customer orders))
    UC11((Generate reports))
    UC12((Download local backup))
    UC13((Review audit and login history))
  end

  Admin --- UC1
  Admin --- UC2
  Admin --- UC3
  Admin --- UC4
  Admin --- UC5
  Admin --- UC6
  Admin --- UC9
  Admin --- UC10
  Admin --- UC11
  Admin --- UC12
  Admin --- UC13

  Cashier --- UC1
  Cashier --- UC2
  Cashier --- UC7
  Cashier --- UC8
  Cashier --- UC10

  Inv --- UC1
  Inv --- UC2
  Inv --- UC4
  Inv --- UC5
  Inv --- UC6
  Inv --- UC10
  Inv --- UC11

  UC7 -. includes .-> UC8
  UC9 -. extends .-> UC7
  UC5 -. includes .-> UC13
  UC11 -. includes .-> UC13

  classDef actor fill:#fff3e0,stroke:#f97316,color:#7c2d12,stroke-width:2px;
  classDef process fill:#eaf3ff,stroke:#2563eb,color:#1e3a8a,stroke-width:2px;
  class Admin,Cashier,Inv actor;
  class UC1,UC2,UC3,UC4,UC5,UC6,UC7,UC8,UC9,UC10,UC11,UC12,UC13 process;
```

## 6. Activity Diagram

```mermaid
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "Inter, Segoe UI, Arial", "lineColor": "#6b7280", "background": "#ffffff"}}}%%
flowchart TD
  A([Begin POS transaction])
  B[Cashier selects product or scans barcode]
  C[Enter quantity]
  D{Product active and not archived?}
  E[Reject item]
  F{Enough stock and batch stock?}
  G[Show insufficient stock message]
  H[Add item to cart]
  I{More items?}
  J[Choose sale channel, payment type, discount, tax]
  K[Calculate subtotal, discount, tax, total]
  L{Payment covers total?}
  M[Request sufficient payment]
  N[Create Sale record]
  O[Create SaleItem records]
  P[Allocate FIFO production batches]
  Q[Deduct product stock]
  R[(Create InventoryLog)]
  S[(Create ActivityLog)]
  T[Render browser receipt / PDF receipt]
  U([End])

  A --> B --> C --> D
  D -- No --> E --> B
  D -- Yes --> F
  F -- No --> G --> B
  F -- Yes --> H --> I
  I -- Yes --> B
  I -- No --> J --> K --> L
  L -- No --> M --> J
  L -- Yes --> N --> O --> P --> Q --> R --> S --> T --> U

  classDef process fill:#eaf3ff,stroke:#2563eb,color:#1e3a8a,stroke-width:2px;
  classDef store fill:#eaf8ef,stroke:#16a34a,color:#14532d,stroke-width:2px;
  classDef decision fill:#fff7cc,stroke:#eab308,color:#713f12,stroke-width:2px;
  classDef actor fill:#fff3e0,stroke:#f97316,color:#7c2d12,stroke-width:2px;
  class A,U actor;
  class B,C,E,G,H,J,K,M,N,O,P,Q,T process;
  class R,S store;
  class D,F,I,L decision;
```

## 7. Sequence Diagram

```mermaid
%%{init: {"theme": "base", "sequence": {"mirrorActors": false}, "themeVariables": {"fontFamily": "Inter, Segoe UI, Arial", "lineColor": "#6b7280", "background": "#ffffff"}}}%%
sequenceDiagram
  actor Cashier
  participant UI as Django Templates / POS UI
  participant View as pos_view
  participant Service as create_sale Service
  participant DB as Database
  participant Inventory as FIFO Inventory Service
  participant Receipt as Receipt / PDF Output

  Cashier->>UI: Select products, quantities, payment, discount, tax
  UI->>View: POST /sales/pos/
  View->>Service: create_sale(cashier, payment, items)
  Service->>DB: Lock active products
  DB-->>Service: Product prices, costs, stock
  Service->>Service: Validate choices, stock, totals, payment
  Service->>DB: Create Sale
  loop For each item
    Service->>DB: Create SaleItem
    Service->>Inventory: allocate_product_stock(product, quantity)
    Inventory->>DB: Lock FIFO ProductionBatch records
    Inventory->>DB: Deduct batch remaining quantity
    Inventory->>DB: Deduct Product.stock_quantity
    Service->>DB: Create InventoryLog
  end
  Service->>DB: Create ActivityLog
  Service-->>View: Sale receipt number
  View-->>UI: Redirect to receipt
  UI->>Receipt: Render receipt or receipt PDF
  Receipt-->>Cashier: Printable receipt
```

## 8. System Architecture Design

```mermaid
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "Inter, Segoe UI, Arial", "lineColor": "#6b7280", "background": "#ffffff"}}}%%
flowchart TB
  subgraph Client[Client Layer]
    Browser([Web browser])
    Static[CSS and JavaScript assets]
  end

  subgraph Presentation[Presentation Layer]
    Templates[Django templates]
    Forms[Validated Django forms]
  end

  subgraph App[Application Layer]
    URLs[URL routing]
    Views[Django views]
    Permissions[RoleRequiredMixin and user_has_role]
    Services[Business services]
    Selectors[Query selectors]
  end

  subgraph Domain[Domain Layer]
    Models[Django models]
    Rules[Validation and constraints]
    Signals[Login and activity signals]
  end

  subgraph Data[Data and External Services]
    DB[(SQLite development / MySQL or PostgreSQL production)]
    Media[(media/products image storage)]
    Email[[Password reset email backend]]
    Exports[(CSV, XLSX, PDF, receipts)]
  end

  Browser --> Static
  Browser --> Templates
  Templates --> Forms
  Forms --> URLs --> Views
  Views --> Permissions
  Views --> Services
  Views --> Selectors
  Services --> Models
  Selectors --> Models
  Models --> Rules
  Signals --> Models
  Models <--> DB
  Models --> Media
  Views --> Email
  Views --> Exports

  classDef actor fill:#fff3e0,stroke:#f97316,color:#7c2d12,stroke-width:2px;
  classDef process fill:#eaf3ff,stroke:#2563eb,color:#1e3a8a,stroke-width:2px;
  classDef store fill:#eaf8ef,stroke:#16a34a,color:#14532d,stroke-width:2px;
  class Browser actor;
  class Static,Templates,Forms,URLs,Views,Permissions,Services,Selectors,Models,Rules,Signals process;
  class DB,Media,Email,Exports store;
```

## 9. Entity Relationship Diagram

```mermaid
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "Inter, Segoe UI, Arial", "lineColor": "#6b7280", "background": "#ffffff"}}}%%
erDiagram
  USER ||--o{ SALE : cashier
  USER ||--o{ SALE : voided_by
  USER ||--o{ ACTIVITY_LOG : performs
  USER ||--o{ LOGIN_HISTORY : has
  USER ||--|| EMPLOYEE_SECURITY : secured_by
  USER ||--o{ PRODUCTION_BATCH : records
  USER ||--o{ INVENTORY_LOG : creates

  CATEGORY ||--o{ PRODUCT : classifies
  SUPPLIER ||--o{ PRODUCT : supplies
  PRODUCT ||--o{ ORDER : requested_in
  PRODUCT ||--o{ SALE_ITEM : sold_as
  PRODUCT ||--o{ VOIDED_SALE_ITEM : restored_as
  PRODUCT ||--o{ INVENTORY_LOG : tracked_by
  PRODUCT ||--o{ PRODUCTION_BATCH : produced_in

  SALE ||--o{ SALE_ITEM : contains
  SALE ||--o{ VOIDED_SALE_ITEM : records
  SALE ||--o{ INVENTORY_LOG : causes
  SALE_ITEM ||--o{ BATCH_ALLOCATION : allocated_by
  PRODUCTION_BATCH ||--o{ BATCH_ALLOCATION : consumed_by

  USER {
    int id PK
    string username UK
    string password
    string email
    bool is_active
  }
  CATEGORY {
    bigint id PK
    string name UK
    string barcode_prefix
    string color
  }
  SUPPLIER {
    bigint id PK
    string name
    string contact_person
    string email
  }
  PRODUCT {
    bigint id PK
    string item_id UK
    string sku UK
    string barcode UK
    bigint category_id FK
    bigint supplier_id FK
    decimal price
    int stock_quantity
  }
  SALE {
    bigint id PK
    string receipt_number UK
    int cashier_id FK
    int voided_by_id FK
    decimal total_amount
    string status
  }
  SALE_ITEM {
    bigint id PK
    bigint sale_id FK
    bigint product_id FK
    int quantity
    decimal line_total
  }
  PRODUCTION_BATCH {
    bigint id PK
    bigint product_id FK
    string batch_number
    int quantity_remaining
  }
  BATCH_ALLOCATION {
    bigint id PK
    bigint sale_item_id FK
    bigint batch_id FK
    int quantity
  }
  ORDER {
    bigint id PK
    bigint product_id FK
    string customer_name
    date pickup_date
    string status
  }
  INVENTORY_LOG {
    bigint id PK
    bigint product_id FK
    bigint sale_id FK
    int user_id FK
    decimal quantity_change
  }
  ACTIVITY_LOG {
    bigint id PK
    int user_id FK
    string action
    json metadata
  }
  LOGIN_HISTORY {
    bigint id PK
    int user_id FK
    string username
    string action
  }
  EMPLOYEE_SECURITY {
    bigint id PK
    int user_id FK
    bool must_change_password
  }
  VOIDED_SALE_ITEM {
    bigint id PK
    bigint sale_id FK
    bigint product_id FK
    int quantity
  }
```

## 10. Database Schema Diagram

```mermaid
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "Inter, Segoe UI, Arial", "lineColor": "#6b7280", "background": "#ffffff"}}}%%
flowchart LR
  subgraph Auth[Authentication and Employees]
    User[(auth_user)]
    Group[(auth_group)]
    UserGroups[(auth_user_groups)]
    EmpSec[(bakery_employeesecurity)]
    Login[(bakery_loginhistory)]
  end

  subgraph Catalog[Catalog]
    Category[(bakery_category)]
    Supplier[(bakery_supplier)]
    Product[(bakery_product)]
  end

  subgraph Transactions[Sales and Orders]
    Sale[(bakery_sale)]
    SaleItem[(bakery_saleitem)]
    VoidItem[(bakery_voidedsaleitem)]
    Order[(bakery_order)]
  end

  subgraph Inventory[Inventory]
    Batch[(bakery_productionbatch)]
    Allocation[(bakery_batchallocation)]
    InvLog[(bakery_inventorylog)]
  end

  subgraph Audit[Audit]
    Activity[(bakery_activitylog)]
    Note[(bakery_note)]
  end

  User --> UserGroups --> Group
  User --> EmpSec
  User --> Login
  User --> Activity
  User --> Sale
  User --> InvLog
  User --> Batch

  Category --> Product
  Supplier --> Product
  Product --> SaleItem
  Product --> VoidItem
  Product --> Order
  Product --> Batch
  Product --> InvLog

  Sale --> SaleItem
  Sale --> VoidItem
  Sale --> InvLog
  SaleItem --> Allocation
  Batch --> Allocation

  classDef store fill:#eaf8ef,stroke:#16a34a,color:#14532d,stroke-width:2px;
  class User,Group,UserGroups,EmpSec,Login,Category,Supplier,Product,Sale,SaleItem,VoidItem,Order,Batch,Allocation,InvLog,Activity,Note store;
```

## 11. Data Dictionary

| Entity | Field Name | Data Type | Description | Constraints | Relationships |
|---|---|---|---|---|---|
| User | id | int | Employee account identifier | PK, auto increment | Referenced by Sale, ActivityLog, InventoryLog, LoginHistory, EmployeeSecurity |
| User | username | varchar(150) | Login username | Unique, required | Used by authentication |
| User | password | varchar(128) | Hashed password | Required | Managed by Django auth |
| User | email | varchar(254) | Account email | Optional in schema | Used by password reset |
| User | is_active | boolean | Account availability | Required | Archived employees set false |
| User | is_superuser / is_staff | boolean | Administrative flags | Required | Enables owner/admin behavior |
| Group | id | int | Role identifier | PK | Connected through auth_user_groups |
| Group | name | varchar(150) | Role name | Unique | Admin, Cashier, Inventory Staff |
| EmployeeSecurity | id | bigint | Security record identifier | PK | One-to-one with User |
| EmployeeSecurity | user_id | int | Secured employee | FK, unique | User.id |
| EmployeeSecurity | must_change_password | boolean | Forces password change after temporary password | Required | Checked after login |
| EmployeeSecurity | temporary_password_created_at | datetime | Temporary password timestamp | Nullable | Set by admin password reset |
| Category | id | bigint | Category identifier | PK | Referenced by Product |
| Category | name | varchar(100) | Category name | Unique, required | Product.category_id |
| Category | barcode_prefix | varchar(12) | SKU/barcode prefix | Auto-filled when blank | Used for product code generation |
| Category | color | varchar(20) | Category display color | Default color | Product theme fallback |
| Supplier | id | bigint | Supplier identifier | PK | Referenced by Product |
| Supplier | name | varchar(150) | Supplier name | Required | Product.supplier_id |
| Supplier | contact_person / phone / email / address | text/varchar | Supplier contact details | Optional | Display and product metadata |
| Product | id | bigint | Product identifier | PK | Referenced by orders, sales, inventory |
| Product | item_id | varchar(30) | Internal item code | Unique, nullable | Auto-generated if blank |
| Product | sku | varchar(50) | Stock keeping unit | Unique, required | Searchable product code |
| Product | barcode | varchar(80) | Barcode value | Unique, nullable | POS barcode lookup |
| Product | name | varchar(150) | Product name | Required | Displayed across modules |
| Product | category_id | bigint | Product category | FK, protected | Category.id |
| Product | supplier_id | bigint | Optional supplier | FK, nullable | Supplier.id |
| Product | price / cost | decimal(10,2) | Selling price and unit cost | Non-negative | Used for totals and profit |
| Product | stock_quantity | positive int | Available stock | Non-negative | Updated by sales, restocks, voids |
| Product | low_stock_threshold | positive int | Low-stock trigger | Non-negative | Dashboard and inventory alerts |
| Product | production_date / expiry_date | date | Product dating metadata | Expiry cannot precede production | Status display |
| Product | is_active / is_archived / is_deleted | boolean | Availability flags | Archived products inactive | Controls sales and orders |
| Product | archived_by_id / archived_at | int/datetime | Archive audit metadata | Nullable FK | User.id |
| ProductionBatch | id | bigint | Batch identifier | PK | Referenced by BatchAllocation |
| ProductionBatch | product_id | bigint | Product produced | FK, required | Product.id |
| ProductionBatch | batch_number | varchar(50) | Batch code | Unique per product | FIFO allocation |
| ProductionBatch | production_date / expiry_date | date | Batch dates | Expiry cannot precede production | FIFO order |
| ProductionBatch | quantity_produced | positive int | Produced amount | >= 1 | Batch capacity |
| ProductionBatch | quantity_remaining | positive int | Remaining amount | >= 0 and <= produced | Deducted by sale allocations |
| ProductionBatch | recorded_by_id | int | User who recorded batch | Nullable FK | User.id |
| BatchAllocation | id | bigint | Allocation identifier | PK | Connects sale items to batches |
| BatchAllocation | sale_item_id | bigint | Sold line item | FK, required | SaleItem.id |
| BatchAllocation | batch_id | bigint | Consumed batch | FK, protected | ProductionBatch.id |
| BatchAllocation | quantity | positive int | Allocated quantity | >= 1 | Restored during void |
| BatchAllocation | restored_at | datetime | Void restoration timestamp | Nullable | Prevents duplicate restoration |
| Sale | id | bigint | Sale identifier | PK | Referenced by SaleItem, VoidedSaleItem, InventoryLog |
| Sale | receipt_number | varchar(30) | Official receipt number | Unique, required | Generated by service |
| Sale | cashier_id | int | Cashier who completed sale | FK, protected | User.id |
| Sale | sale_channel | varchar(20) | walk_in or online | Choice constraint | POS input |
| Sale | payment_type | varchar(20) | cash, gcash, maya, card | Choice constraint | POS input |
| Sale | subtotal / discount_amount / tax_amount / total_amount | decimal(12,2) | Financial totals | Non-negative | Report and receipt totals |
| Sale | tax_rate | decimal(5,4) | Tax rate | 0 to 1 | Used in total calculation |
| Sale | payment_amount / change_amount | decimal(12,2) | Payment and change | Non-negative | Payment must cover total |
| Sale | status | varchar(20) | completed or voided | Choice constraint | Void workflow |
| Sale | voided_by_id / voided_at / void_reason | int/datetime/text | Void approval details | Nullable except reason during void | User.id |
| SaleItem | id | bigint | Sale line identifier | PK | Referenced by BatchAllocation |
| SaleItem | sale_id | bigint | Parent sale | FK cascade | Sale.id |
| SaleItem | product_id | bigint | Sold product | FK protected | Product.id |
| SaleItem | quantity | positive int | Quantity sold | >= 1 | Deducts stock |
| SaleItem | unit_price / unit_cost / line_total | decimal | Sale line pricing | Non-negative | Profit and receipts |
| VoidedSaleItem | id | bigint | Voided line identifier | PK | Created when sale is voided |
| VoidedSaleItem | sale_id / product_id | bigint | Voided transaction and product | FKs | Sale.id, Product.id |
| VoidedSaleItem | quantity / unit_price / line_total | int/decimal | Restored item details | Positive or non-negative | Stock restoration evidence |
| VoidedSaleItem | reason | varchar(255) | Void reason | Required | Admin approval record |
| Order | id | bigint | Customer order identifier | PK | Optional Product reference |
| Order | customer_name / contact | varchar | Customer details | Required | Order fulfillment |
| Order | product_id | bigint | Requested product | Nullable FK | Product.id |
| Order | order_date / pickup_date | date | Order and pickup dates | pickup_date >= order_date | Scheduling rule |
| Order | quantity | positive int | Ordered quantity | >= 1 | Estimated total |
| Order | estimated_total | decimal(12,2) | Estimated order value | Non-negative | Order display |
| Order | status | varchar(20) | pending, in_progress, completed, claimed, cancelled | Controlled transitions | Workflow state |
| InventoryLog | id | bigint | Inventory history identifier | PK, append-only | Product and sale movements |
| InventoryLog | item_type | varchar(20) | Inventory item type | product only | Future extension point |
| InventoryLog | action | varchar(20) | restock, sale, adjustment, void | Choice constraint | Movement classification |
| InventoryLog | reason | varchar(30) | restock, damaged, expired, returned, sampling, staff_consumption | Choice/blank | Deduction explanation |
| InventoryLog | product_id / sale_id / user_id | bigint/int | Movement references | Nullable FKs | Product.id, Sale.id, User.id |
| InventoryLog | quantity_before / quantity_change / quantity_after | decimal(12,2) | Stock movement amounts | Required | Audit trail |
| ActivityLog | id | bigint | Activity identifier | PK, append-only | User activity audit |
| ActivityLog | user_id | int | Acting user | Nullable FK | User.id |
| ActivityLog | action | varchar(20) | login, logout, create, update, delete, archive, stock, sale, void, backup, restore, password | Choice constraint | Audit classification |
| ActivityLog | model_name / object_id / object_repr | varchar/text | Affected object metadata | Optional | Generic audit reference |
| ActivityLog | ip_address / metadata | IP/json | Request and structured details | Nullable/default JSON | Security review |
| LoginHistory | id | bigint | Login event identifier | PK, append-only | Authentication audit |
| LoginHistory | user_id | int | Related account | Nullable FK | User.id |
| LoginHistory | username | varchar(150) | Attempted username | Optional | Failed login tracking |
| LoginHistory | action | varchar(20) | login, logout, failed | Choice constraint | Auth event status |
| LoginHistory | ip_address / user_agent | IP/varchar | Client request details | Optional | Monitoring |
| Note | id | bigint | Note identifier | PK | Standalone dashboard/content note |
| Note | title / content | varchar/text | Note content | Required | Informational |
| Note | is_active | boolean | Note visibility | Required | Active note filtering |

## 12. Relationship Mapping Diagram

```mermaid
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "Inter, Segoe UI, Arial", "lineColor": "#6b7280", "background": "#ffffff"}}}%%
flowchart TB
  User[(User)]
  Group[(Group)]
  EmpSec[(EmployeeSecurity)]
  Login[(LoginHistory)]
  Activity[(ActivityLog)]

  Category[(Category)]
  Supplier[(Supplier)]
  Product[(Product)]
  Order[(Order)]

  Sale[(Sale)]
  SaleItem[(SaleItem)]
  VoidItem[(VoidedSaleItem)]

  Batch[(ProductionBatch)]
  Allocation[(BatchAllocation)]
  InvLog[(InventoryLog)]

  User --- Group
  User --- EmpSec
  User --- Login
  User --- Activity
  User --- Sale
  User --- Batch
  User --- InvLog

  Category --- Product
  Supplier --- Product
  Product --- Order
  Product --- SaleItem
  Product --- VoidItem
  Product --- Batch
  Product --- InvLog

  Sale --- SaleItem
  Sale --- VoidItem
  Sale --- InvLog
  SaleItem --- Allocation
  Batch --- Allocation

  classDef store fill:#eaf8ef,stroke:#16a34a,color:#14532d,stroke-width:2px;
  class User,Group,EmpSec,Login,Activity,Category,Supplier,Product,Order,Sale,SaleItem,VoidItem,Batch,Allocation,InvLog store;
```

## Workflow and API Route Summary

| Module | Main Routes | Primary Inputs | Primary Outputs |
|---|---|---|---|
| Authentication | `/login/`, `/logout/`, `/password-reset/`, `/password-change-required/` | credentials, reset email, new password | session, login history, password activity log |
| Employee management | `/employees/`, `/employees/add/`, `/employees/<id>/edit/`, `/employees/<id>/password/` | account details, role, temporary password request | user record, employee security record, activity log |
| Catalog | `/categories/`, `/products/`, `/suppliers/` | category, product, supplier data | catalog records, product image references, activity log |
| Inventory | `/inventory/`, `/products/<id>/restock/`, `/production/` | stock changes, production batch details | updated stock, production batches, inventory logs |
| Sales | `/sales/pos/`, `/sales/`, `/sales/<id>/receipt/`, `/sales/<id>/void/`, `/sales/<id>/receipt.pdf` | cart items, payment, sale channel, discount, tax, void reason | sale, sale items, stock deduction/restoration, receipts |
| Orders | `/orders/`, `/orders/add/`, `/orders/<id>/edit/` | customer, contact, product, quantity, pickup date | tracked order status |
| Reports and backup | `/reports/`, `/reports/sales.csv`, `/reports/sales.xlsx`, `/reports/sales.pdf`, `/backup/database/` | report request, backup request | exports, local SQLite backup, activity log |
| Audit | `/audit/activity/`, `/audit/logins/` | filters/search from UI | activity history, login history |

