# System Instructions For Printing Facility Inventory App

## Overview
A web-based inventory management system designed for high-volume printing facilities. Tracks production materials including paper rolls, printer toner, machine oil, maintenance supplies, and spare parts. The application provides real-time stock monitoring, low-stock alerts, usage tracking, and bulk import/export capabilities.

## Architecture

### Backend
- **Framework**: Flask 3.1.2
- **Database**: SQLite (inventory.db)
- **Language**: Python 3.x
- **ORM**: Raw SQL queries using sqlite3

### Frontend
- **UI Framework**: Bootstrap 5.3.0
- **Icons**: Font Awesome 6.0.0
- **Template Engine**: Jinja2 3.1.6
- **JavaScript**: Vanilla JS for search, filtering, and real-time updates

### Dependencies (requirements.txt)
```
blinker==1.9.0
click==8.2.1
Flask==3.1.2
itsdangerous==2.2.0
Jinja2==3.1.6
MarkupSafe==3.0.2
Werkzeug==3.1.3
```

## Core Features

### 1. Inventory Management
- **Add Items**: Create new inventory items with detailed specifications
- **Edit Items**: Update existing item information including quantities
- **Delete Items**: Remove items and associated usage history
- **View Dashboard**: Overview with summary cards showing total items, low stock count, and categories

### 2. Stock Tracking
- **Real-time Monitoring**: Auto-refresh stock status every 30-60 seconds
- **Visual Indicators**: Color-coded rows and progress bars for stock levels
  - Red (Out of Stock): quantity = 0
  - Yellow (Low Stock): quantity ≤ minimum_threshold
  - Blue (Good Stock): quantity > minimum_threshold
- **Usage Recording**: Track when items are used with quantity and notes
- **Usage History**: Historical record of all item usage

### 3. Low Stock Alerts
- **Alert Badge**: Navbar badge shows count of low-stock items
- **Low Stock Page**: Dedicated view for items at or below minimum threshold
- **Automatic Detection**: Items flagged when current_quantity ≤ minimum_threshold

### 4. Search & Filter
- **Text Search**: Real-time search across item names
- **Category Filter**: Filter inventory by category
- **Combined Filtering**: Search and category filters work together

### 5. Data Import/Export
- **CSV Import**: Bulk import items from CSV files
- **CSV Export**: Download current inventory as CSV with timestamp
- **Expected CSV Format**: name, category, current_quantity, minimum_threshold, unit, supplier, notes

### 6. Categories & Units
**Predefined Categories**:
- Toner & Ink
- Paper & Media
- Machine Oil
- Maintenance
- Tools
- Cleaning Supplies
- Spare Parts
- Other (with custom input)

**Supported Units**:
pieces, bottles, cartridges, liters, gallons, boxes, packs, rolls, sheets, kg, lbs

## Database Schema

### Table: `inventory`
```sql
CREATE TABLE inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    current_quantity INTEGER NOT NULL DEFAULT 0,
    minimum_threshold INTEGER NOT NULL DEFAULT 0,
    unit TEXT NOT NULL DEFAULT 'pieces',
    supplier TEXT,
    notes TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Table: `usage_history`
```sql
CREATE TABLE usage_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER,
    quantity_used INTEGER,
    remaining_quantity INTEGER,
    date_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (item_id) REFERENCES inventory (id)
)
```

## API Endpoints

### Web Routes
1. **`GET /`** - Dashboard/Index page with all inventory items
2. **`GET/POST /add_item`** - Form to add new inventory items
3. **`GET/POST /edit_item/<int:item_id>`** - Edit existing item details
4. **`GET/POST /use_item/<int:item_id>`** - Record item usage and update quantity
5. **`GET /low_stock`** - Display items at or below minimum threshold
6. **`GET/POST /import_csv`** - Upload and import items from CSV file
7. **`GET /export_csv`** - Download current inventory as CSV
8. **`GET /delete_item/<int:item_id>`** - Delete item and its usage history

### REST API Endpoints
9. **`GET /api/stock_status`** - JSON endpoint for stock status
   - Returns: `total_items`, `low_stock_count`, `low_stock_items` array

## Technical Debt

### Critical Bugs (Must Fix)
1. **Line 24 in app.py**: Typo in table name - `CREATE TABLE IF NOT EXISTS iventory` should be `inventory`
2. **Line 83 in app.py**: Typo in table name - `UPDATE iventory SET` should be `UPDATE inventory`
3. **Line 83 in app.py**: Extra comma before WHERE clause - `last_updated = ?, WHERE` should be `last_updated = ? WHERE`
4. **Line 69 in app.py**: Missing parentheses on function call - `.fetchone` should be `.fetchone()`
5. **Line 70 in app.py**: Missing parentheses on function call - `conn.close` should be `conn.close()`

### Missing Implementations
- **use_item.html**: Template file is empty (line 1 blank)
- **low_stock.html**: Template file is empty (line 1 blank)
- **import_csv.html**: Template file is empty (line 1 blank)
- **edit_item.html**: Template file is empty (line 1 blank)

### Code Quality Issues
- **No input validation**: Server-side validation missing for forms
- **No error handling**: Database operations lack try-catch blocks
- **SQL injection risk**: Some queries use direct string formatting (minimal risk with current code but should use parameterized queries consistently)
- **No logging**: Application lacks proper logging for debugging and audit trails

## Next Steps

### High Priority (Critical Fixes)
- [ ] Fix database table name typos in app.py (lines 24, 83)
- [ ] Fix SQL syntax error on line 83 (extra comma)
- [ ] Fix missing function call parentheses (lines 69-70)
- [ ] Implement missing template files (use_item.html, low_stock.html, import_csv.html, edit_item.html)

### Medium Priority (Functionality)
- [ ] Add usage history view page to display historical usage data
- [ ] Create usage report export (filtered by date range, item, or category)
- [ ] Add pagination for large inventory lists
- [ ] Implement item restock functionality (separate from edit)
- [ ] Add barcode/QR code scanning support for quick item lookup

### Future Enhancements
- [ ] User authentication and authorization system
- [ ] Role-based access control (admin, manager, staff)
- [ ] Email/SMS notifications for low stock alerts
- [ ] Dashboard analytics with charts and graphs
- [ ] Supplier management module
- [ ] Purchase order tracking
- [ ] Integration with accounting systems
- [ ] Mobile-responsive improvements
- [ ] Dark mode theme
- [ ] Multi-location/warehouse support
- [ ] Automated reorder suggestions based on usage patterns
- [ ] API authentication for external integrations

## Development Guidelines

### Running the Application
```bash
# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py

# Access at: http://localhost:5000
```

### Coding Standards
- Follow PEP 8 style guidelines for Python code
- Use meaningful variable and function names
- Add docstrings for functions and classes
- Keep functions focused and under 50 lines when possible
- Use parameterized SQL queries to prevent SQL injection

### Testing Requirements
- Test all CRUD operations manually before committing
- Verify CSV import with various file formats
- Test low stock alerts with different threshold values
- Validate form inputs on both client and server side
- Test edge cases (empty inventory, zero quantities, special characters)

### Deployment Process
1. Update requirements.txt if dependencies change
2. Test thoroughly in development environment
3. Backup inventory.db before deploying
4. Set `debug=False` in production
5. Use production-grade WSGI server (Gunicorn, uWSGI)
6. Set secure secret_key (not hardcoded)
7. Enable HTTPS for production
8. Set up regular database backups

## Notes

### Current State
- Application is functional with known bugs in app.py
- Four template files need implementation to complete core features
- Database is working and contains data (modified in git status)
- No authentication system - open access to all features

### Security Considerations
- Secret key is hardcoded - should use environment variable
- No authentication - anyone can access and modify inventory
- No CSRF protection on forms
- Running with debug=True and host='0.0.0.0' is not production-safe

### Performance Notes
- SQLite is suitable for small to medium deployments
- Consider PostgreSQL/MySQL for larger deployments or concurrent users
- Current implementation doesn't have connection pooling
- Frontend auto-refresh may cause unnecessary server load with many clients

### Backup Strategy
- Database file: `inventory.db` (currently modified and not staged)
- Regular backups recommended before major changes
- Export CSV periodically as a backup mechanism