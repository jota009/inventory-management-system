from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import os
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'SGCInventoryApp2025'


@app.context_processor
def inject_low_stock_count():
    low_stock_items = get_low_stock_items()
    return dict(low_stock_count=len(low_stock_items))

# Database Initialization
def init_db():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()

    # Create inventory table
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT,
            current_quantity INTEGER NOT NULL DEFAULT 0,
            minimum_threshold INTEGER NOT NULL DEFAULT 0,
            unit TEXT NOT NULL DEFAULT 'pieces',
            supplier TEXT,
            notes TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create usage history table
    c.execute('''
        CREATE TABLE IF NOT EXISTS usage_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            quantity_used INTEGER,
            remaining_quantity INTEGER,
            date_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (item_id) REFERENCES inventory (id)
        )
    ''')

    # Seed sample data if database is empty
    c.execute('SELECT COUNT(*) FROM inventory')
    if c.fetchone()[0] == 0:
        sample_items = [
            # Toner Cartridges for RICOH Pro C9200 (52K yield)
            ('RICOH Type C9200 Toner - Black', 'Toner & Ink', '', 8, 4, 'cartridges', 'Ricoh Direct', '52,000 page yield for Pro C9200'),
            ('RICOH Type C9200 Toner - Cyan', 'Toner & Ink', '', 3, 4, 'cartridges', 'Ricoh Direct', 'Low stock - 52K yield'),
            ('RICOH Type C9200 Toner - Magenta', 'Toner & Ink', '', 5, 4, 'cartridges', 'Ricoh Direct', '52,000 page yield'),
            ('RICOH Type C9200 Toner - Yellow', 'Toner & Ink', '', 4, 4, 'cartridges', 'Ricoh Direct', '52,000 page yield'),
            # Paper Rolls for Continuous Feed
            ('Xerographic Bond 22" x 500ft Roll', 'Paper & Media', '', 12, 6, 'rolls', 'Ricoh Consumables', '20lb rolls, 2 per carton'),
            ('Xerographic Bond 36" x 500ft Roll', 'Paper & Media', '', 6, 3, 'rolls', 'Ricoh Consumables', '20lb 92 bright, wide format'),
            ('Glossy Cover Stock 18" Roll', 'Paper & Media', '', 4, 2, 'rolls', 'Ricoh Consumables', 'For color brochures and marketing'),
            # Machine Oil & Maintenance Supplies
            ('Fuser Oil - Silicone Based', 'Machine Oil', '', 5, 3, 'bottles', 'Precision Roller Supply', '500ml bottles for fuser maintenance'),
            ('Drive Gear Lubricant', 'Machine Oil', '', 3, 2, 'tubes', 'Precision Roller Supply', 'For internal mechanical components'),
            # Spare Parts (High-wear consumables for Pro C9200)
            ('Photo Conductor Drum M2059510', 'Spare Parts', 'PC Drum', 2, 3, 'pieces', 'Ricoh Direct', 'OEM drum for Pro C9200 - critical low stock'),
            ('Fuser Unit Assembly C9200', 'Spare Parts', 'Fuser Roll', 1, 2, 'pieces', 'Ricoh Direct', 'Complete fuser assembly'),
            ('Developer Unit - Black', 'Spare Parts', 'Developer Unit', 3, 2, 'pieces', 'Ricoh Direct', 'Developer for black toner'),
            ('IBT Belt Transfer Unit', 'Spare Parts', 'Transfer Roller', 2, 2, 'pieces', 'Precision Roller Supply', 'Intermediate belt transfer'),
            ('Feed Roller Assembly', 'Spare Parts', 'Feed Roller', 6, 3, 'pieces', 'Precision Roller Supply', 'Paper feed mechanism'),
            ('Waste Toner Container', 'Spare Parts', 'Waste Toner Bottle', 10, 4, 'pieces', 'Ricoh Direct', 'Collects waste toner'),
            # Cleaning Supplies
            ('IPA Cleaning Solution 99%', 'Cleaning Supplies', '', 8, 4, 'bottles', 'Industrial Supply Co', '1L isopropyl alcohol for drum cleaning'),
            ('Lint-Free Wipes Industrial', 'Cleaning Supplies', '', 20, 10, 'boxes', 'Industrial Supply Co', '200 wipes per box'),
            ('Anti-Static Cleaning Kit', 'Cleaning Supplies', '', 12, 6, 'kits', 'Industrial Supply Co', 'Prevents static buildup on rollers'),
            # Out of Stock Item (showcases alert system)
            ('RICOH Type C9200 Toner - Yellow', 'Toner & Ink', '', 0, 4, 'cartridges', 'Ricoh Direct', 'OUT OF STOCK - urgent reorder needed'),
        ]

        c.executemany(
            'INSERT INTO inventory (name, category, subcategory, current_quantity, minimum_threshold, unit, supplier, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            sample_items
        )

    conn.commit()
    conn.close()

# Database helper functions
def get_db_connection():
    conn = sqlite3.connect('inventory.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_all_items():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM inventory ORDER BY name').fetchall()
    conn.close()
    return items

def get_item_by_id(item_id):
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM inventory WHERE id = ?', (item_id,)).fetchone()
    conn.close()
    return item

def get_low_stock_items():
    conn = get_db_connection()
    items = conn.execute(
        'SELECT * FROM inventory WHERE current_quantity <= minimum_threshold ORDER BY name'
    ).fetchall()
    conn.close()
    return items

def update_item_quantity(item_id, new_quantity):
    conn = get_db_connection()
    conn.execute('UPDATE inventory SET current_quantity = ?, last_updated = ? WHERE id = ?',
                (new_quantity, datetime.now(), item_id)
    )
    conn.commit()
    conn.close()

def record_usage(item_id, quantity_used, remaining_quantity, notes=""):
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO usage_history (item_id, quantity_used, remaining_quantity, notes) VALUES (?, ?, ?, ?)',
        (item_id, quantity_used, remaining_quantity, notes)
    )
    conn.commit()
    conn.close()

# Routes
@app.route('/')
def index():
    items = get_all_items()
    low_stock_items = get_low_stock_items()
    return render_template('index.html', items=items, low_stock_count=len(low_stock_items))

@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        # Extract form data
        name = request.form['name']
        category = request.form['category']
        # Get subcategory from form (optional field - returns empty string if not provided)
        subcategory = request.form.get('subcategory', '')
        current_quantity = int(request.form['current_quantity'])
        minimum_threshold = int(request.form['minimum_threshold'])
        unit = request.form['unit']
        supplier = request.form['supplier']
        notes = request.form['notes']

        conn = get_db_connection()
        # UPDATED: Added subcategory column to INSERT statement
        conn.execute(
            'INSERT INTO inventory (name, category, subcategory, current_quantity, minimum_threshold, unit, supplier, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (name, category, subcategory, current_quantity, minimum_threshold, unit, supplier, notes)
        )
        conn.commit()
        conn.close()

        flash('Item added succesfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_item.html')

@app.route('/edit_item/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    item = get_item_by_id(item_id)

    if request.method == 'POST':
        # Extract form data
        name = request.form['name']
        category = request.form['category']
        # Get subcategory from form (optional field - returns empty string if not provided)
        subcategory = request.form.get('subcategory', '')
        current_quantity = int(request.form['current_quantity'])
        minimum_threshold = int(request.form['minimum_threshold'])
        unit = request.form['unit']
        supplier = request.form['supplier']
        notes = request.form['notes']

        conn = get_db_connection()
        # UPDATED: Added subcategory column to UPDATE statement
        conn.execute(
            'UPDATE inventory SET name=?, category=?, subcategory=?, current_quantity=?, minimum_threshold=?, unit=?, supplier=?, notes=?, last_updated=? WHERE id=?',
            (name, category, subcategory, current_quantity, minimum_threshold, unit, supplier, notes, datetime.now(), item_id)
        )
        conn.commit()
        conn.close()

        flash('Item updated successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('edit_item.html', item=item)

@app.route('/use_item/<int:item_id>', methods=['POST'])
def use_item(item_id):
    """
    Use Item Route - AJAX Endpoint

    Purpose:
        Handles one-click usage of inventory items via AJAX POST request.
        Decreases item quantity by 1 and logs the usage to history.

    How it works:
        1. Receives POST request with item_id in URL
        2. Gets current item data from database
        3. Validates that item has stock available (current_quantity > 0)
        4. If valid:
           - Decreases quantity by 1
           - Updates inventory table
           - Records usage in usage_history table
           - Returns JSON success response
        5. If invalid:
           - Returns JSON error response

    Returns:
        JSON object with format:
        {
            "success": true/false,
            "new_quantity": <number>,      (only if success)
            "message": "<user message>",
            "item_name": "<name>",         (only if success)
            "item_id": <id>                (only if success)
        }

    Usage:
        Called from JavaScript AJAX in index.html when user clicks minus button
    """
    # Get the item from database
    item = get_item_by_id(item_id)

    # Check if item exists
    if not item:
        return jsonify({
            'success': False,
            'message': 'Item not found'
        }), 404

    # Fixed quantity for one-click usage (always 1)
    quantity_used = 1

    # Optional notes from AJAX request (empty string if not provided)
    # This allows future enhancement for adding notes
    notes = request.json.get('notes', '') if request.is_json else ''

    # ========================================
    # VALIDATION: Check if enough stock available
    # ========================================
    if quantity_used > item['current_quantity']:
        # Not enough stock - return error response
        return jsonify({
            'success': False,
            'message': f'Cannot use item: only {item["current_quantity"]} {item["unit"]} available!'
        }), 400

    # If stock is zero, also reject (edge case)
    if item['current_quantity'] == 0:
        return jsonify({
            'success': False,
            'message': 'Cannot use item: out of stock!'
        }), 400

    # ========================================
    # UPDATE INVENTORY
    # ========================================
    # Calculate new quantity after usage
    # Example: If current is 10 and we use 1, new quantity is 9
    new_quantity = item['current_quantity'] - quantity_used

    # Update the inventory table with new quantity
    # This also updates the last_updated timestamp
    update_item_quantity(item_id, new_quantity)

    # ========================================
    # RECORD USAGE HISTORY
    # ========================================
    # Log this usage event to the usage_history table
    # This keeps track of when items were used for reporting/auditing
    record_usage(item_id, quantity_used, new_quantity, notes)

    # ========================================
    # RETURN SUCCESS RESPONSE
    # ========================================
    # Return JSON response that JavaScript will use to update the page
    return jsonify({
        'success': True,
        'new_quantity': new_quantity,
        'message': f'Used {quantity_used} {item["unit"]} of {item["name"]}. Remaining: {new_quantity}',
        'item_name': item['name'],
        'item_id': item_id
    }), 200

@app.route('/restock_item/<int:item_id>', methods=['POST'])
def restock_item(item_id):
    """
    Restock Item Route - AJAX Endpoint

    Purpose:
        Handles one-click restocking of inventory items via AJAX POST request.
        Increases item quantity by 1.

    Returns:
        JSON object with format:
        {
            "success": true/false,
            "new_quantity": <number>,
            "message": "<user message>",
            "item_name": "<name>",
            "item_id": <id>
        }
    """
    item = get_item_by_id(item_id)

    if not item:
        return jsonify({
            'success': False,
            'message': 'Item not found'
        }), 404

    # Get quantity to add (default 1)
    quantity_added = request.json.get('quantity', 1) if request.is_json else 1

    # Calculate new quantity
    new_quantity = item['current_quantity'] + quantity_added

    # Update the inventory table
    update_item_quantity(item_id, new_quantity)

    return jsonify({
        'success': True,
        'new_quantity': new_quantity,
        'message': f'Added {quantity_added} {item["unit"]} to {item["name"]}. New quantity: {new_quantity}',
        'item_name': item['name'],
        'item_id': item_id
    }), 200

@app.route('/low_stock')
def low_stock():
    items = get_low_stock_items()
    return render_template('low_stock.html', items=items)

@app.route('/usage_history')
def usage_history():
    conn = get_db_connection()
    # Get all usage history with item details
    history = conn.execute('''
        SELECT uh.*, i.name as item_name, i.category, i.unit
        FROM usage_history uh
        JOIN inventory i ON uh.item_id = i.id
        ORDER BY uh.date_used DESC
        LIMIT 100
    ''').fetchall()
    conn.close()
    return render_template('usage_history.html', history=history)

@app.route('/usage_history/<int:item_id>')
def item_usage_history(item_id):
    item = get_item_by_id(item_id)
    if not item:
        flash('Item not found', 'error')
        return redirect(url_for('index'))

    conn = get_db_connection()
    history = conn.execute('''
        SELECT * FROM usage_history
        WHERE item_id = ?
        ORDER BY date_used DESC
    ''', (item_id,)).fetchall()
    conn.close()
    return render_template('item_usage_history.html', item=item, history=history)



@app.route('/delete_item/<int:item_id>')
def delete_item(item_id):
    conn = get_db_connection()
    # Also delete usage history
    conn.execute('DELETE FROM usage_history WHERE item_id = ?', (item_id,))
    conn.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()

    flash('Item deleted successfully!', 'success')
    return redirect(url_for('index'))

# API endpoint for quick stock check
@app.route('/api/stock_status')
def api_stock_status():
    items = get_all_items()
    low_stock = get_low_stock_items()

    return jsonify({
        'total_items': len(items),
        'low_stock_count': len(low_stock),
        'low_stock_items': [{'name': item['name'], 'current': item['current_quantity'], 'minimum': item['minimum_threshold']} for item in low_stock]
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
