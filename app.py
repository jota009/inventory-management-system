from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import csv
import io
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
        name = request.form['name']
        category = request.form['category']
        current_quantity = int(request.form['current_quantity'])
        minimum_threshold = int(request.form['minimum_threshold'])
        unit = request.form['unit']
        supplier = request.form['supplier']
        notes = request.form['notes']

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO inventory (name, category, current_quantity, minimum_threshold, unit, supplier, notes) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (name, category, current_quantity, minimum_threshold, unit, supplier, notes)
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
        name = request.form['name']
        category = request.form['category']
        current_quantity = int(request.form['current_quantity'])
        minimum_threshold = int(request.form['minimum_threshold'])
        unit = request.form['unit']
        supplier = request.form['supplier']
        notes = request.form['notes']

        conn = get_db_connection()
        conn.execute(
            'UPDATE inventory SET name=?, category=?, current_quantity=?, minimum_threshold=?, unit=?, supplier=?, notes=?, last_updated=? WHERE id=?',
            (name, category, current_quantity, minimum_threshold, unit, supplier, notes, datetime.now(), item_id)
        )
        conn.commit()
        conn.close()

        flash('Item updated successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('edit_item.html', item=item)

@app.route('/use_item/<int:item_id>', methods=['GET', 'POST'])
def use_item(item_id):
    item = get_item_by_id(item_id)

    if request.method == 'POST':
        quantity_used = int(request.form['quantity_used'])
        notes = request.form.get('notes', '')

        if quantity_used > item['current_quantity']:
            flash('Cannot use more items than available in stock!', 'error')
            return render_template('use_item.html', item=item)

        new_quantity = item['current_quantity'] - quantity_used
        update_item_quantity(item_id, new_quantity)
        record_usage(item_id, quantity_used, new_quantity, notes)

        flash(f'Used {quantity_used} {item["unit"]} of {item["name"]}. Remaining: {new_quantity}', 'success')
        return redirect(url_for('index'))

    return render_template('use_item.html', item=item)

@app.route('/low_stock')
def low_stock():
    items = get_low_stock_items()
    return render_template('low_stock.html', items=items)

@app.route('/import_csv', methods=['GET', 'POST'])
def import_csv():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        if file and file.filename.endswith('.csv'):
            try:
                stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                csv_reader = csv.DictReader(stream)

                conn = get_db_connection()
                imported_count = 0

                for row in csv_reader:
                    name = row.get('name', '').strip()
                    category = row.get('category', 'General').strip()
                    current_quantity = int(row.get('current_quantity', 0))
                    minimum_threshold = int(row.get('minimum_threshold', 0))
                    unit = row.get('unit', 'pieces').strip()
                    supplier = row.get('supplier', '').strip()
                    notes = row.get('notes', '').strip()

                    if name:  # Only import if name is provided
                        conn.execute(
                            'INSERT INTO inventory (name, category, current_quantity, minimum_threshold, unit, supplier, notes) VALUES (?, ?, ?, ?, ?, ?, ?)',
                            (name, category, current_quantity, minimum_threshold, unit, supplier, notes)
                        )
                        imported_count += 1

                conn.commit()
                conn.close()

                flash(f'Successfully imported {imported_count} items!', 'success')
                return redirect(url_for('index'))

            except Exception as e:
                flash(f'Error importing CSV: {str(e)}', 'error')
        else:
            flash('Please upload a CSV file', 'error')

    return render_template('import_csv.html')

@app.route('/export_csv')
def export_csv():
    items = get_all_items()

    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['name', 'category', 'current_quantity', 'minimum_threshold', 'unit', 'supplier', 'notes'])

    # Write data
    for item in items:
        writer.writerow([
            item['name'], item['category'], item['current_quantity'],
            item['minimum_threshold'], item['unit'], item['supplier'], item['notes']
        ])

    output.seek(0)

    from flask import Response
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=inventory_export_{datetime.now().strftime("%Y%m%d")}.csv'}
    )

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