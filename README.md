# Bakery Sales and Inventory System

A Django-based bakery management app for point-of-sale, product inventory, orders, suppliers, and reporting.

## Features

- Role-aware dashboard for Admin, Cashier, and Inventory Staff
- Database-based user accounts
- Dynamic login system
- Role-based access control
- Product, supplier, employee, production batch, and order management
- Product images, unique SKU/item ID/barcode values, supplier/date metadata, archive support, and category colors
- POS workflow with barcode lookup, walk-in/online sale type, discounts, tax, and automatic product stock deduction
- Admin-approved sale voids with automatic stock restoration and voided-item records
- Inventory history logs and low-stock alerts
- Audit trail/logs and login history
- Session timeout
- SQL injection protection through Django ORM queries and validated forms
- Forgot-password email flow
- Password hashing and password complexity checks
- Sales reporting with PDF, Excel, and CSV exports
- Printable browser receipt and PDF receipt output
- SQLite for development with MySQL and PostgreSQL environment support
- Backup download and restore upload for the SQLite database

## Setup

```bash
python -m pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py seed_bakery_demo
python manage.py createsuperuser
python manage.py runserver
```

## User Accounts

Accounts are stored in the database. Create the first admin with `python manage.py createsuperuser`, then use the Employees screen to add staff and assign Admin, Cashier, or Inventory Staff roles.

## Database Configuration

Set these environment variables to switch from SQLite to MySQL:

- `MYSQL_DB`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_HOST`
- `MYSQL_PORT`

If `MYSQL_DB` is not set, you can still switch to PostgreSQL with:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

## Email Configuration

By default, password reset emails are written to the console during development. Set these environment variables to send real password reset email:

- `DJANGO_EMAIL_BACKEND`
- `DJANGO_EMAIL_HOST`
- `DJANGO_EMAIL_PORT`
- `DJANGO_EMAIL_HOST_USER`
- `DJANGO_EMAIL_HOST_PASSWORD`
- `DJANGO_EMAIL_USE_TLS`
- `DJANGO_DEFAULT_FROM_EMAIL`

## Notes

- The seed command creates user roles and starter product categories only. It does not create hard-coded user accounts.
- Owner/superuser accounts cannot be deleted or archived, and the last active admin account cannot lose Admin access.
- Uploaded product images are stored in `media/products/`.
- The backup download route is intended for SQLite backups in development or small deployments.
- Passwords must be at least 8 characters and include uppercase, lowercase, number, and special character, such as `Example@123`.
