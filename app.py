from flask import Flask, render_template, request, redirect, jsonify, url_for
import sqlite3
import json

app = Flask(__name__)

# ---------------------- Database Helper Functions ----------------------
def get_real_dashboard_data():
    try:
        conn = sqlite3.connect('toy_store.db')
        c = conn.cursor()
        
        # Get total sales
        c.execute('SELECT SUM(amount) FROM daily_sales')
        total_sales_result = c.fetchone()[0]
        total_sales = total_sales_result if total_sales_result else 0
        
        # Get total expenses
        c.execute('SELECT SUM(amount) FROM vendor_details')
        total_expenses_result = c.fetchone()[0]
        total_expenses = total_expenses_result if total_expenses_result else 0
        
        # Get staff and vendor counts
        c.execute('SELECT COUNT(*) FROM staff')
        staff_count = c.fetchone()[0]
        
        c.execute('SELECT COUNT(DISTINCT name) FROM vendor_details')
        vendor_count = c.fetchone()[0]
        
        # Get recent sales
        c.execute('SELECT date, product_name, amount, mode_of_transaction, transaction_id FROM daily_sales ORDER BY date DESC LIMIT 10')
        recent_sales = c.fetchall()
        
        # Get chart data - daily sales totals
        c.execute('SELECT date, SUM(amount) FROM daily_sales GROUP BY date ORDER BY date DESC LIMIT 7')
        chart_raw = c.fetchall()
        
        # Format chart data for Chart.js
        chart_labels = [row[0] for row in reversed(chart_raw)]
        chart_values = [float(row[1]) for row in reversed(chart_raw)]
        
        chart_data = {
            'labels': chart_labels,
            'data': chart_values
        }
        
        sales_chart = list(reversed(chart_raw))
        
        conn.close()
        
        return {
            'total_sales': total_sales,
            'total_expenses': total_expenses,
            'staff_count': staff_count,
            'vendor_count': vendor_count,
            'recent_sales': recent_sales,
            'sales_chart': sales_chart,
            'chart_data': json.dumps(chart_data)
        }
        
    except Exception as e:
        print(f"Database error: {e}")
        return {
            'total_sales': 0,
            'total_expenses': 0,
            'staff_count': 0,
            'vendor_count': 0,
            'recent_sales': [],
            'sales_chart': [],
            'chart_data': json.dumps({'labels': [], 'data': []})
        }
# ---------------------- Homepage ----------------------
@app.route('/')
def home():
    dashboard_data = get_real_dashboard_data()
    return render_template('admin_dashboard.html', **dashboard_data)

@app.route('/admin')
def admin_dashboard():
    dashboard_data = get_real_dashboard_data()
    return render_template('admin_dashboard.html', **dashboard_data)

# ---------------------- Daily Sales ----------------------
@app.route('/daily_sales_log')
def daily_sales_log():
    conn = sqlite3.connect('toy_store.db')
    c = conn.cursor()
    c.execute('SELECT * FROM daily_sales')
    sales = c.fetchall()
    conn.close()
    return render_template('daily_sales_log.html', sales=sales)

@app.route('/update_sale', methods=['POST'])
def update_sale():
    data = request.get_json()
    conn = sqlite3.connect('toy_store.db')
    c = conn.cursor()
    c.execute('''
        UPDATE daily_sales
        SET date = ?, product_id = ?, product_name = ?, amount = ?, mode_of_transaction = ?, transaction_id = ?
        WHERE id = ?
    ''', (data['date'], data['product_id'], data['product_name'], data['amount'], data['mode_of_transaction'], data['transaction_id'], data['id']))
    conn.commit()
    conn.close()
    return '', 204

# ---------------------- Monthly Tracker ----------------------
@app.route('/monthly_tracker')
def monthly_tracker_view():
    conn = sqlite3.connect('toy_store.db')
    c = conn.cursor()
    c.execute('SELECT * FROM monthly_tracker ORDER BY id DESC')
    monthly = c.fetchall()

    profit = 0
    for entry in monthly:
        profit += (entry[4] or 0) - (entry[3] or 0)

    conn.close()
    return render_template('monthly_tracker.html', monthly=monthly, profit=profit)

@app.route('/add_monthly', methods=['POST'])
def add_monthly():
    data = request.get_json()
    conn = sqlite3.connect('toy_store.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO monthly_tracker (month, total_sales, total_expenses, net_profit)
        VALUES (?, ?, ?, ?)
    ''', (data['month'], data['total_sales'], data['total_expenses'], data['net_profit']))
    conn.commit()
    conn.close()
    return '', 204

@app.route('/update_monthly', methods=['POST'])
def update_monthly():
    data = request.get_json()
    conn = sqlite3.connect('toy_store.db')
    c = conn.cursor()
    c.execute('''
        UPDATE monthly_tracker
        SET month = ?, total_sales = ?, total_expenses = ?, net_profit = ?
        WHERE id = ?
    ''', (data['month'], data['total_sales'], data['total_expenses'], data['net_profit'], data['id']))
    conn.commit()
    conn.close()
    return '', 204

# ---------------------- Vendor Details ----------------------
@app.route('/vendor_details')
def vendor_details():
    conn = sqlite3.connect('toy_store.db')
    c = conn.cursor()
    c.execute('SELECT id, date, name, item, amount, vendor_id, mode_of_transaction, transaction_id FROM vendor_details ORDER BY date DESC')
    vendors = c.fetchall()
    conn.close()
    return render_template('vendor_details.html', vendors=vendors)

@app.route('/add_vendor', methods=['POST'])
def add_vendor():
    date = request.form.get('date', '')
    name = request.form.get('name', '')
    item = request.form.get('item', '')
    amount = request.form.get('amount', 0)
    mode_of_transaction = request.form.get('mode_of_transaction', '')
    
    import time
    vendor_id = f"V{int(time.time())}"
    transaction_id = f"TXN{int(time.time())}"
    
    conn = sqlite3.connect('toy_store.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO vendor_details (date, name, item, amount, vendor_id, mode_of_transaction, transaction_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (date, name, item, amount, vendor_id, mode_of_transaction, transaction_id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('vendor_details'))

@app.route('/update_vendor', methods=['POST'])
def update_vendor():
    data = request.get_json()
    conn = sqlite3.connect('toy_store.db')
    c = conn.cursor()
    c.execute('''
        UPDATE vendor_details
        SET date = ?, name = ?, item = ?, amount = ?, vendor_id = ?, mode_of_transaction = ?, transaction_id = ?
        WHERE id = ?
    ''', (data['date'], data['name'], data['item'], data['amount'], data['vendor_id'], data['mode_of_transaction'], data['transaction_id'], data['id']))
    conn.commit()
    conn.close()
    return '', 204

@app.route('/delete_vendor', methods=['POST'])
def delete_vendor():
    data = request.get_json()
    conn = sqlite3.connect('toy_store.db')
    c = conn.cursor()
    c.execute('DELETE FROM vendor_details WHERE id = ?', (data['id'],))
    conn.commit()
    conn.close()
    return '', 204

# ---------------------- Staff Records ----------------------
@app.route('/staff_record')
def staff_record():
    conn = sqlite3.connect('toy_store.db')
    c = conn.cursor()
    c.execute('SELECT * FROM staff')
    staffs = c.fetchall()
    conn.close()
    return render_template('staff_record.html', staffs=staffs)

@app.route('/add_staff', methods=['POST'])
def add_staff():
    data = request.get_json()
    conn = sqlite3.connect('toy_store.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO staff (staff_name, position, salary, contact_number)
        VALUES (?, ?, ?, ?)
    ''', (data['name'], data['position'], data.get('salary'), data.get('contact')))
    conn.commit()
    conn.close()
    return '', 204

@app.route('/update_staff', methods=['POST'])
def update_staff():
    data = request.get_json()
    conn = sqlite3.connect('toy_store.db')
    c = conn.cursor()
    c.execute('''
        UPDATE staff
        SET staff_name = ?, position = ?, salary = ?, contact_number = ?
        WHERE staff_id = ?
    ''', (data['name'], data['position'], data['salary'], data['contact'], data['id']))
    conn.commit()
    conn.close()
    return '', 204

# ---------------------- Product API ----------------------
@app.route('/get_products')
def get_products():
    conn = sqlite3.connect('toy_store.db')
    c = conn.cursor()
    c.execute('SELECT product_id, product_name, price, quantity FROM products')
    products = c.fetchall()
    conn.close()
    return jsonify([
        {'id': pid, 'name': pname, 'price': price, 'quantity': quantity}
        for pid, pname, price, quantity in products
    ])

@app.route('/add_product', methods=['POST'])
def add_product():
    data = request.get_json()
    conn = sqlite3.connect('toy_store.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO products (product_id, product_name, price, quantity)
        VALUES (?, ?, ?, ?)
    ''', (data['product_id'], data['product_name'], data['price'], data['quantity']))
    conn.commit()
    conn.close()
    return '', 204

@app.route('/update_daily_sales', methods=['POST'])
def update_daily_sales():
    data = request.form
    conn = sqlite3.connect('toy_store.db')
    c = conn.cursor()
    c.execute('''
        UPDATE daily_sales
        SET date = ?, product_id = ?, product_name = ?, amount = ?, mode_of_transaction = ?, transaction_id = ?
        WHERE id = ?
    ''', (data['date'], data['product_id'], data['product_name'], data['amount'], data['mode_of_transaction'], data['transaction_id'], data['id']))
    conn.commit()
    conn.close()
    return '', 204

@app.route('/add_daily_sales', methods=['POST'])
def add_daily_sales():
    try:
        data = request.form
        conn = sqlite3.connect('toy_store.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO daily_sales (date, product_id, product_name, amount, mode_of_transaction, transaction_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['date'], data['product_id'], data['product_name'], float(data['amount']), data['mode_of_transaction'], data['transaction_id']))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------- Run App ----------------------
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)