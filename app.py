from flask import Flask, render_template_string, request, redirect, url_for, jsonify, session
import sqlite3
import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'ladyboss_secret_2026' # Change this to something random
DB_NAME = 'ladyboss.db'

# --- AUTHENTICATION DECORATOR ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Products
    c.execute('''CREATE TABLE IF NOT EXISTS products 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, barcode TEXT, name TEXT, category TEXT, cost REAL, price REAL, stock INTEGER)''')
    # Sales
    c.execute('''CREATE TABLE IF NOT EXISTS sales 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, total REAL, discount REAL, method TEXT, date TEXT)''')
    # Expenses
    c.execute('''CREATE TABLE IF NOT EXISTS expenses 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT, amount REAL, date TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- HTML TEMPLATES (Mobile Responsive + Chart.js) ---
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Login - The Lady Boss</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>body { background: #1e1e24; color: white; }</style>
</head>
<body class="d-flex align-items-center justify-content-center" style="height: 100vh;">
    <div class="card p-4 shadow" style="width: 350px; border-radius: 15px; background: #2d2d35; color: white;">
        <h3 class="text-center mb-4" style="color: #00bcd4;">The Lady Boss</h3>
        {% if error %}<div class="alert alert-danger p-2 text-center">{{ error }}</div>{% endif %}
        <form method="POST">
            <div class="mb-3"><label>Username</label><input type="text" name="username" class="form-control" required></div>
            <div class="mb-3"><label>Password</label><input type="password" name="password" class="form-control" required></div>
            <button type="submit" class="btn btn-info w-100 text-white fw-bold">LOGIN</button>
        </form>
    </div>
</body>
</html>
"""

BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Lady Boss POS</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { background-color: #f4f6f9; font-family: 'Segoe UI', sans-serif; }
        .sidebar { background: #212529; color: white; min-height: 100vh; }
        .sidebar a { color: #adb5bd; text-decoration: none; padding: 15px 20px; display: block; font-weight: 500; }
        .sidebar a:hover, .sidebar a.active { background: #0d6efd; color: white; border-left: 4px solid white; }
        .card-custom { border: none; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        .stat-card { color: white; border-radius: 10px; padding: 15px; }
        @media (max-width: 768px) {
            .sidebar { min-height: auto; display: flex; overflow-x: auto; padding: 0; }
            .sidebar a { padding: 10px 15px; font-size: 14px; white-space: nowrap; }
        }
    </style>
</head>
<body>
    <div class="container-fluid p-0">
        <div class="row g-0">
            <!-- Sidebar -->
            <div class="col-md-2 sidebar d-none d-md-block">
                <h4 class="text-center py-4 mb-0 text-white fw-bold">The Lady Boss</h4>
                <a href="/" class="{{ 'active' if active == 'dashboard' }}">📊 Dashboard</a>
                <a href="/pos" class="{{ 'active' if active == 'pos' }}">🛒 POS Billing</a>
                <a href="/inventory" class="{{ 'active' if active == 'inventory' }}">📦 Inventory</a>
                <a href="/expenses" class="{{ 'active' if active == 'expenses' }}">💸 Expenses</a>
                <a href="/logout" class="text-danger mt-5">🚪 Logout</a>
            </div>
            <!-- Mobile Top Nav -->
            <div class="d-md-none bg-dark d-flex justify-content-between p-3">
                <span class="text-white fw-bold">Lady Boss</span>
                <a href="/logout" class="text-danger text-decoration-none">Logout</a>
            </div>
            <div class="d-md-none bg-secondary d-flex overflow-auto">
                <a href="/" class="text-white text-decoration-none p-2 small">Home</a>
                <a href="/pos" class="text-white text-decoration-none p-2 small">POS</a>
                <a href="/inventory" class="text-white text-decoration-none p-2 small">Stock</a>
                <a href="/expenses" class="text-white text-decoration-none p-2 small">Expenses</a>
            </div>

            <!-- Main Content -->
            <div class="col-md-10 p-3 p-md-4">
                {% block content %}{% endblock %}
            </div>
        </div>
    </div>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
{% extends "base" %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h3 class="fw-bold">Welcome, Admin 👋</h3>
    <span class="badge bg-primary">{{ today_date }}</span>
</div>

<div class="row mb-4">
    <div class="col-6 col-md-3 mb-2">
        <div class="stat-card bg-primary">
            <small>Today's Sales</small>
            <h4 class="fw-bold mb-0">LKR {{ today_sales }}</h4>
        </div>
    </div>
    <div class="col-6 col-md-3 mb-2">
        <div class="stat-card bg-success">
            <small>Gross Profit</small>
            <h4 class="fw-bold mb-0">LKR {{ today_profit }}</h4>
        </div>
    </div>
    <div class="col-6 col-md-3 mb-2">
        <div class="stat-card bg-warning text-dark">
            <small>Today's Expenses</small>
            <h4 class="fw-bold mb-0">LKR {{ today_expenses }}</h4>
        </div>
    </div>
    <div class="col-6 col-md-3 mb-2">
        <div class="stat-card bg-dark">
            <small>Net Profit</small>
            <h4 class="fw-bold mb-0 text-info">LKR {{ net_profit }}</h4>
        </div>
    </div>
</div>

<div class="card card-custom p-4 bg-white">
    <h5 class="mb-3">Sales Last 7 Days</h5>
    <canvas id="salesChart" height="80"></canvas>
</div>

<script>
    const ctx = document.getElementById('salesChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: {{ chart_labels|safe }},
            datasets: [{
                label: 'Sales (LKR)',
                data: {{ chart_data|safe }},
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: { responsive: true }
    });
</script>
{% endblock %}
"""

POS_TEMPLATE = """
{% extends "base" %}
{% block content %}
<div class="row">
    <!-- Products Panel -->
    <div class="col-md-7 mb-3">
        <div class="card card-custom p-3">
            <input type="text" id="barcode-search" class="form-control form-control-lg mb-3" placeholder="Scan Barcode or Search Product..." onkeyup="searchProducts()">
            <div class="row" id="product-grid">
                {% for p in products %}
                <div class="col-6 col-md-4 mb-2 product-card" data-name="{{ p[2]|lower }}" data-barcode="{{ p[1] }}">
                    <div class="card p-2 text-center h-100 cursor-pointer shadow-sm" onclick="addToCart({{ p[0] }}, '{{ p[2] }}', {{ p[5] }}, {{ p[6] }})">
                        <div class="fw-bold small">{{ p[2] }}</div>
                        <div class="text-muted small">{{ p[1] }}</div>
                        <div class="text-primary fw-bold mt-1">LKR {{ p[6] }}</div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
    
    <!-- Cart Panel -->
    <div class="col-md-5">
        <div class="card card-custom p-3 bg-white h-100">
            <h5 class="fw-bold border-bottom pb-2">Current Order</h5>
            <div id="cart-list" class="mb-3" style="max-height: 300px; overflow-y: auto;"></div>
            
            <div class="mt-auto">
                <div class="d-flex justify-content-between mb-2">
                    <span>Subtotal:</span>
                    <span id="subtotal" class="fw-bold">LKR 0.00</span>
                </div>
                <div class="d-flex justify-content-between mb-2">
                    <span>Discount (%):</span>
                    <input type="number" id="discount" class="form-control w-25 text-end" value="0" onchange="updateCartUI()">
                </div>
                <h4 class="d-flex justify-content-between border-top pt-2 text-success">
                    <span>Total:</span>
                    <span id="total">LKR 0.00</span>
                </h4>
                <button class="btn btn-success w-100 py-2 fw-bold mt-2" onclick="checkout()">PAY & PRINT BILL</button>
            </div>
        </div>
    </div>
</div>

<script>
    let cart = {};
    let total = 0;

    function searchProducts() {
        let input = document.getElementById('barcode-search').value.toLowerCase();
        let cards = document.querySelectorAll('.product-card');
        cards.forEach(card => {
            let name = card.getAttribute('data-name');
            let barcode = card.getAttribute('data-barcode');
            if(name.includes(input) || barcode === input) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
        
        // Auto-add if exact barcode match (Simulate Scanner)
        let exactMatch = Array.from(cards).find(c => c.getAttribute('data-barcode') === input);
        if(exactMatch && input.length > 3) {
            exactMatch.querySelector('.card').click();
            document.getElementById('barcode-search').value = '';
            searchProducts();
        }
    }

    function addToCart(id, name, cost, price) {
        if(cart[id]) { cart[id].qty += 1; } 
        else { cart[id] = {name: name, price: price, cost: cost, qty: 1}; }
        updateCartUI();
    }

    function removeFromCart(id) { delete cart[id]; updateCartUI(); }

    function updateCartUI() {
        let list = document.getElementById('cart-list');
        list.innerHTML = '';
        let subtotal = 0;
        
        for(let id in cart) {
            let item = cart[id];
            let itemTotal = item.price * item.qty;
            subtotal += itemTotal;
            list.innerHTML += `
                <div class="d-flex justify-content-between align-items-center border-bottom py-2">
                    <div>
                        <div class="fw-bold small">${item.name}</div>
                        <small class="text-muted">${item.qty} x LKR ${item.price}</small>
                    </div>
                    <div class="text-end">
                        <div class="fw-bold text-primary">LKR ${itemTotal.toFixed(2)}</div>
                        <button class="btn btn-sm btn-outline-danger py-0 px-2 mt-1" onclick="removeFromCart(${id})">Remove</button>
                    </div>
                </div>`;
        }
        
        let discountPct = document.getElementById('discount').value || 0;
        let discountAmt = subtotal * (discountPct / 100);
        let finalTotal = subtotal - discountAmt;
        
        document.getElementById('subtotal').innerText = `LKR ${subtotal.toFixed(2)}`;
        document.getElementById('total').innerText = `LKR ${finalTotal.toFixed(2)}`;
        total = finalTotal;
    }

    function checkout() {
        if(Object.keys(cart).length === 0) return alert("Cart is empty!");
        fetch('/process_checkout', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({cart: cart, total: total})
        }).then(res => res.json()).then(data => {
            if(data.success) { 
                alert("Payment Successful! Bill Saved."); 
                cart = {}; 
                document.getElementById('discount').value = 0;
                updateCartUI(); 
                window.location.reload(); 
            }
        });
    }
</script>
{% endblock %}
"""

INVENTORY_TEMPLATE = """
{% extends "base" %}
{% block content %}
<div class="d-flex justify-content-between mb-3">
    <h3 class="fw-bold">Inventory</h3>
    <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addModal">+ Add Item</button>
</div>
<div class="card card-custom p-3 bg-white table-responsive">
    <table class="table table-hover align-middle">
        <thead class="table-light">
            <tr><th>Barcode</th><th>Name</th><th>Category</th><th>Cost</th><th>Price</th><th>Margin</th><th>Stock</th></tr>
        </thead>
        <tbody>
            {% for p in products %}
            <tr>
                <td>{{ p[1] }}</td><td class="fw-bold">{{ p[2] }}</td><td>{{ p[3] }}</td>
                <td>{{ p[4] }}</td><td class="text-primary fw-bold">{{ p[5] }}</td>
                <td class="text-success">{{ "%.1f"|format(((p[5]-p[4])/p[5])*100 if p[5] > 0 else 0) }}%</td>
                <td><span class="badge {{ 'bg-danger' if p[6] < 5 else 'bg-success' }}">{{ p[6] }}</span></td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

<!-- Add Modal -->
<div class="modal fade" id="addModal" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <form action="/add_product" method="POST">
        <div class="modal-header"><h5 class="modal-title">Add Product</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
        <div class="modal-body">
            <div class="mb-2"><label>Barcode</label><input type="text" name="barcode" class="form-control"></div>
            <div class="mb-2"><label>Name</label><input type="text" name="name" class="form-control" required></div>
            <div class="mb-2"><label>Category</label><input type="text" name="category" class="form-control"></div>
            <div class="mb-2"><label>Cost Price (LKR)</label><input type="number" step="0.01" name="cost" class="form-control" required></div>
            <div class="mb-2"><label>Selling Price (LKR)</label><input type="number" step="0.01" name="price" class="form-control" required></div>
            <div class="mb-2"><label>Stock</label><input type="number" name="stock" class="form-control" required></div>
        </div>
        <div class="modal-footer"><button type="submit" class="btn btn-success">Save</button></div>
      </form>
    </div>
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
{% endblock %}
"""

# --- ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        # CHANGE CREDENTIALS HERE
        if request.form['username'] == 'admin' and request.form['password'] == 'ladyboss123':
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else: error = 'Invalid Credentials'
    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    today = datetime.date.today().strftime('%Y-%m-%d')
    
    # Today's Sales & Profit
    c.execute("SELECT SUM(total) FROM sales WHERE date LIKE ?", (f"{today}%",))
    today_sales = c.fetchone()[0] or 0.0
    
    # Today's Expenses
    c.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE ?", (f"{today}%",))
    today_expenses = c.fetchone()[0] or 0.0
    
    # Dummy Profit Calculation (In real app, calculate from sale_items)
    today_profit = today_sales * 0.3 
    net_profit = today_profit - today_expenses

    # Chart Data (Last 7 Days)
    labels = []
    data = []
    for i in range(6, -1, -1):
        d = datetime.date.today() - datetime.timedelta(days=i)
        d_str = d.strftime('%Y-%m-%d')
        labels.append(f"'{d.strftime('%b %d')}'")
        c.execute("SELECT SUM(total) FROM sales WHERE date LIKE ?", (f"{d_str}%",))
        data.append(c.fetchone()[0] or 0)
        
    conn.close()
    
    html = render_template_string(BASE_TEMPLATE.replace("{% block content %}{% endblock %}", DASHBOARD_TEMPLATE.replace("{% extends \"base\" %}", "").replace("{% block content %}", "").replace("{% endblock %}", "")), 
                                  active='dashboard', today_date=today, today_sales=f"{today_sales:.2f}", 
                                  today_profit=f"{today_profit:.2f}", today_expenses=f"{today_expenses:.2f}", net_profit=f"{net_profit:.2f}",
                                  chart_labels=f"[{','.join(labels)}]", chart_data=f"[{','.join(map(str,data))}]")
    return html

@app.route('/inventory')
@login_required
def inventory():
    conn = sqlite3.connect(DB_NAME)
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return render_template_string(BASE_TEMPLATE.replace("{% block content %}{% endblock %}", INVENTORY_TEMPLATE.replace("{% extends \"base\" %}", "").replace("{% block content %}", "").replace("{% endblock %}", "")), 
                                  active='inventory', products=products)

@app.route('/add_product', methods=['POST'])
@login_required
def add_product():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("INSERT INTO products (barcode, name, category, cost, price, stock) VALUES (?,?,?,?,?,?)", 
                 (request.form['barcode'], request.form['name'], request.form['category'], float(request.form['cost']), float(request.form['price']), int(request.form['stock'])))
    conn.commit(); conn.close()
    return redirect(url_for('inventory'))

@app.route('/pos')
@login_required
def pos():
    conn = sqlite3.connect(DB_NAME)
    products = conn.execute("SELECT * FROM products WHERE stock > 0").fetchall()
    conn.close()
    return render_template_string(BASE_TEMPLATE.replace("{% block content %}{% endblock %}", POS_TEMPLATE.replace("{% extends \"base\" %}", "").replace("{% block content %}", "").replace("{% endblock %}", "")), 
                                  active='pos', products=products)

@app.route('/process_checkout', methods=['POST'])
@login_required
def process_checkout():
    data = request.json
    conn = sqlite3.connect(DB_NAME)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("INSERT INTO sales (total, discount, method, date) VALUES (?, ?, ?, ?)", (data['total'], 0, 'Cash', now))
    for p_id, item in data['cart'].items():
        conn.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (item['qty'], p_id))
    conn.commit(); conn.close()
    return jsonify({"success": True})

@app.route('/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    conn = sqlite3.connect(DB_NAME)
    if request.method == 'POST':
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("INSERT INTO expenses (description, amount, date) VALUES (?, ?, ?)", (request.form['desc'], float(request.form['amount']), now))
        conn.commit()
    exps = conn.execute("SELECT * FROM expenses ORDER BY id DESC").fetchall()
    conn.close()
    
    html = f"""
    <h3 class="fw-bold mb-3">Expenses</h3>
    <div class="card p-3 bg-white mb-3"><form method="POST" class="d-flex gap-2">
        <input type="text" name="desc" class="form-control" placeholder="Description" required>
        <input type="number" step="0.01" name="amount" class="form-control w-25" placeholder="Amount" required>
        <button class="btn btn-danger">Add</button>
    </form></div>
    <div class="card p-3 bg-white"><table class="table"><tr><th>Date</th><th>Description</th><th>Amount</th></tr>
    """
    for e in exps: html += f"<tr><td>{e[3]}</td><td>{e[1]}</td><td class='text-danger fw-bold'>LKR {e[2]:.2f}</td></tr>"
    html += "</table></div>"
    
    return render_template_string(BASE_TEMPLATE.replace("{% block content %}{% endblock %}", html), active='expenses')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)