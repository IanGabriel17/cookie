# Bakery Sales and Inventory System

A Django-based bakery management app for point-of-sale, inventory, ingredients, orders, suppliers, and reporting.

## Features

- Role-aware dashboard for Admin, Cashier, and Inventory Staff
- Product, ingredient, recipe, supplier, and order management
- POS workflow with automatic product and ingredient deduction
- Inventory history logs and low-stock alerts
- Sales reporting with PDF and Excel exports
- Printable browser receipt and PDF receipt output
- SQLite for development with MySQL and PostgreSQL environment support
- Backup download for the SQLite database

## Setup

```bash
python -m pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py seed_bakery_demo
python manage.py runserver
```

## Demo Accounts

- `admin` / `admin1234`
- `cashier` / `cashier1234`
- `inventory` / `inventory1234`

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

## Notes

- The seed command only creates user roles and login accounts. Products, stock items, suppliers, and transactions should be created through the app.
- Uploaded product images are stored in `media/products/`.
- The backup download route is intended for SQLite backups in development or small deployments.
