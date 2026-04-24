# Inventory Management System (Python Tkinter + SQLite)

A production-oriented desktop Inventory Management System for a retail shop with role-based access, real-time stock tracking, sales workflow, reporting, and backup/restore.

## Stack (Option A)
- **Language:** Python 3
- **GUI:** Tkinter (modern themed widgets)
- **Database:** SQLite

## Features Implemented

### Core Features
- Add, update, delete, and search products
- Product category management
- Real-time stock quantity tracking
- Low-stock alerts dashboard
- Sales transaction recording
- Invoice/receipt generation (`receipts/receipt_sale_<id>.txt`)
- Sales history
- Daily, weekly, and monthly sales reports
- Profit calculation (per sale + per report)

### User Roles
- **Admin:** Full control (products, categories, sales, reports, backup/restore)
- **Staff:** Sales + product viewing (category management disabled)

### GUI
- Clean desktop interface with sidebar navigation
- Dashboard metrics:
  - Total products
  - Total stock units
  - Today’s sales count
  - Today’s revenue/profit
- Forms for products, categories, sales
- Data tables for inventory, low stock, transactions, and cart

### Additional Features
- Barcode scanning support via barcode field/lookup (USB scanner-compatible)
- Export reports to CSV and PDF
- Login authentication system
- Input validation and error handling
- Backup and restore database
- Dark mode toggle
- In-app notifications (status bar + alerts)
- Multi-shop support (shop selected during login)

## Project Structure
- `inventory_management_system/app.py` - application entry point
- `inventory_management_system/ui.py` - GUI and interactions
- `inventory_management_system/database.py` - SQLite schema + data access/business persistence
- `inventory_management_system/services.py` - receipt/export/backup services
- `inventory_management_system/schema.sql` - database schema reference

## Setup Instructions
1. Ensure Python 3.10+ is installed.
2. Navigate to the repository root, then run:
   ```bash
   python3 inventory_management_system/app.py
   ```
3. Login using default credentials:
   - Username: `admin`
   - Password: `admin123`
4. Select a shop (`Main Shop` is seeded automatically).

## GUI Preview Explanation
- **Login Screen:** Username/password + shop selector.
- **Dashboard:** Key business metrics and low-stock alerts.
- **Products:** Product CRUD + search by name/barcode/SKU.
- **Categories:** Category CRUD (admin).
- **Sales:** Add item by product dropdown or barcode, complete transaction, auto-receipt generation.
- **History:** All recorded transactions with revenue/profit.
- **Reports:** Daily/weekly/monthly reports with CSV/PDF export.

## Notes
- Database file is created at: `inventory_management_system/inventory.db`
- Export outputs:
  - `inventory_management_system/exports/`
  - `inventory_management_system/receipts/`
  - `inventory_management_system/backups/`
