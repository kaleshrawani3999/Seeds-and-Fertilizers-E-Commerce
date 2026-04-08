import pandas as pd
from flask import Flask, render_template, request, redirect, flash, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# ---------------- MYSQL CONNECTION HELPER ----------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="its.pdv.0410",
        database="indumai"
    )

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s,%s,%s)",
            (name, email, hashed_password)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['logged_in'] = True
            session['user_id'] = user['id']
            flash("Login successful!", "success")
            return redirect(url_for('products'))
        else:
            flash("Invalid email or password.", "error")
            return redirect(url_for('login'))

    return render_template('login.html')

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('login'))

# ---------------- PRODUCTS ----------------
@app.route('/products')
def products():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products")
    products_list = cursor.fetchall()

    cart_count = 0
    if session.get('logged_in'):
        cursor.execute("SELECT SUM(quantity) as total FROM cart WHERE user_id=%s", (session['user_id'],))
        result = cursor.fetchone()
        cart_count = result['total'] if result['total'] else 0

    cursor.close()
    conn.close()
    return render_template("products.html", products=products_list, cart_count=cart_count)

# ---------------- ADD TO CART ----------------
@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT quantity FROM cart WHERE user_id=%s AND product_id=%s",
        (user_id, product_id)
    )
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            "UPDATE cart SET quantity = quantity + 1 WHERE user_id=%s AND product_id=%s",
            (user_id, product_id)
        )
    else:
        cursor.execute(
            "INSERT INTO cart (user_id, product_id, quantity) VALUES (%s,%s,%s)",
            (user_id, product_id, 1)
        )

    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('cart_page'))
# ---------------- BUY NOW ----------------
@app.route('/buy_now', methods=['POST'])
def buy_now():

    # CHECK LOGIN
    if 'user_id' not in session:
        flash("Please login first to buy products.")
        return redirect(url_for('login'))

    user_id = session['user_id']
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT quantity FROM cart WHERE user_id=%s AND product_id=%s",
        (user_id, product_id)
    )

    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            "UPDATE cart SET quantity = quantity + %s WHERE user_id=%s AND product_id=%s",
            (quantity, user_id, product_id)
        )
    else:
        cursor.execute(
            "INSERT INTO cart (user_id, product_id, quantity) VALUES (%s,%s,%s)",
            (user_id, product_id, quantity)
        )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('cart_page'))
# ---------------- CART PAGE ----------------
@app.route('/cart')
def cart_page():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT products.id, products.name, products.price, products.image, cart.quantity
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.user_id = %s
    """, (session['user_id'],))

    cart_items = cursor.fetchall()

    total = sum(float(item['price']) * int(item['quantity']) for item in cart_items)

    cursor.close()
    conn.close()

    return render_template('cart.html', cart_items=cart_items, total=total)
# ---------------- UPDATE CART ----------------
@app.route('/update_cart', methods=['POST'])
def update_cart():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session['user_id']
    product_id = request.form.get('product_id')
    action = request.form.get('action')

    conn = get_db_connection()
    cursor = conn.cursor()

    if action == 'increase':
        cursor.execute(
            "UPDATE cart SET quantity = quantity + 1 WHERE user_id=%s AND product_id=%s",
            (user_id, product_id)
        )
    elif action == 'decrease':
        cursor.execute(
            "UPDATE cart SET quantity = quantity - 1 WHERE user_id=%s AND product_id=%s",
            (user_id, product_id)
        )
        cursor.execute(
            "DELETE FROM cart WHERE user_id=%s AND product_id=%s AND quantity <= 0",
            (user_id, product_id)
        )
    elif action == 'remove':
        cursor.execute(
            "DELETE FROM cart WHERE user_id=%s AND product_id=%s",
            (user_id, product_id)
        )

    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('cart_page'))
# ---------------- WISHLIST TOGGLE ----------------

@app.route('/toggle_wishlist/<int:product_id>')
def toggle_wishlist(product_id):

    if 'user_id' not in session:
        return {"status": "login_required"}

    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM wishlist WHERE user_id=%s AND product_id=%s",
        (user_id, product_id)
    )

    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            "DELETE FROM wishlist WHERE user_id=%s AND product_id=%s",
            (user_id, product_id)
        )
        status = "removed"

    else:
        cursor.execute(
            "INSERT INTO wishlist (user_id, product_id) VALUES (%s,%s)",
            (user_id, product_id)
        )
        status = "added"

    conn.commit()

    cursor.close()
    conn.close()

    return {"status": status}
#-------------------------------------------------------
@app.route('/wishlist')
def wishlist():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT products.*
        FROM wishlist
        JOIN products ON wishlist.product_id = products.id
        WHERE wishlist.user_id=%s
    """,(session['user_id'],))

    items = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("wishlist.html", items=items)

# ---------------- CHECKOUT ----------------
@app.route('/checkout', methods=['POST'])
def checkout():

    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session['user_id']
    district = request.form.get('district')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT cart.product_id, cart.quantity, products.price
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.user_id=%s
    """, (user_id,))

    items = cursor.fetchall()   # IMPORTANT: must have ()

    if not items:
        flash("Your cart is empty!", "error")
        cursor.close()
        conn.close()
        return redirect(url_for('cart_page'))

    total_amount = sum(
        int(item['quantity']) * float(item['price']) for item in items
    )

    cursor.execute("""
        INSERT INTO orders (user_id, total_amount, status, current_location, district)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, total_amount, 'Pending', 'Processing', district))

    order_id = cursor.lastrowid

    for item in items:
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, price)
            VALUES (%s, %s, %s, %s)
        """, (
            order_id,
            item['product_id'],
            item['quantity'],
            item['price']
        ))

    cursor.execute("DELETE FROM cart WHERE user_id=%s", (user_id,))

    conn.commit()
    cursor.close()
    conn.close()

    flash(f"Order placed successfully! Total amount: ₹{total_amount}", "success")

    return redirect(url_for('orders'))
# ---------------- ORDERS ----------------
@app.route('/orders')
def orders():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
    SELECT 
        orders.id,
        orders.created_at,
        orders.status,
        order_items.quantity,
        order_items.price,
        products.name,
        products.image,
        products.id as product_id
    FROM orders
    JOIN order_items ON orders.id = order_items.order_id
    JOIN products ON order_items.product_id = products.id
    WHERE orders.user_id = %s
    ORDER BY orders.created_at DESC
    """, (session['user_id'],))

    rows = cursor.fetchall()

    orders = {}

    for row in rows:
        order_id = row['id']

        if order_id not in orders:
            orders[order_id] = {
                "id": row['id'],
                "created_at": row['created_at'],
                "status": row['status'],
                "items": []
            }

        orders[order_id]["items"].append({
            "name": row['name'],
            "price": row['price'],
            "quantity": row['quantity'],
            "image": row['image'],
            "product_id": row['product_id']
        })

    cursor.close()
    conn.close()

    return render_template("orders.html", orders=list(orders.values()))
# ---------------- ORDER TRACKING ----------------
@app.route('/track_order/<int:order_id>')
def track_order(order_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM orders WHERE id=%s AND user_id=%s",
        (order_id, session['user_id'])
    )

    order = cursor.fetchone()

    cursor.close()
    conn.close()

    if not order:
        flash("Order not found.", "error")
        return redirect(url_for('orders'))

    return render_template("track_order.html", order=order)

# ---------------- REVIEWS ----------------

@app.route('/add_review/<int:product_id>', methods=['POST'])
def add_review(product_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    rating = request.form['rating']
    review = request.form['review']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO reviews (user_id, product_id, rating, review)
    VALUES (%s,%s,%s,%s)
    """,(session['user_id'], product_id, rating, review))

    conn.commit()

    cursor.close()
    conn.close()

    flash("Review added")
    return redirect(url_for('products'))
# ---------------- RETURN REQUEST ----------------

@app.route('/request_return/<int:order_id>/<int:product_id>', methods=['POST'])
def request_return(order_id, product_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    reason = request.form['reason']
    return_type = request.form['type']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO returns (order_id, product_id, user_id, reason, type)
    VALUES (%s,%s,%s,%s,%s)
    """,(order_id, product_id, session['user_id'], reason, return_type))

    conn.commit()

    cursor.close()
    conn.close()

    flash("Return request submitted")
    return redirect(url_for('orders'))

# ---------------- CONTACT ----------------
@app.route('/contact', methods=['GET','POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO contact (name, email, message) VALUES (%s, %s, %s)",
            (name, email, message)
        )

        conn.commit()
        cursor.close()
        conn.close()

        flash("Message received successfully!", "success")
        return redirect(url_for('contact'))

    return render_template('contact.html')
# ---------------- DELETE CONTACT MESSAGE ----------------
@app.route('/admin/delete_message/<int:msg_id>')
def delete_message(msg_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM contact WHERE id=%s", (msg_id,))
    conn.commit()

    cursor.close()
    conn.close()

    flash("Message deleted successfully!", "success")
    return redirect(url_for('admin_panel'))
    
# ---------------- STATIC PAGES ----------------
@app.route("/")
def home():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM products LIMIT 8")
    products = cursor.fetchall()
    cart_count = 0
    if session.get('logged_in'):
        cursor.execute("SELECT SUM(quantity) as total FROM cart WHERE user_id=%s", (session['user_id'],))
        result = cursor.fetchone()
        cart_count = result['total'] if result and result['total'] else 0
    cursor.close()
    conn.close()
    return render_template("index.html", products=products, cart_count=cart_count)

# ---------------- ADMIN LOGIN ----------------
@app.route('/admin_login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s AND is_admin=1", (email,))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()

        if admin and check_password_hash(admin['password'], password):
            session['admin_logged_in'] = True
            flash("Admin logged in", "success")
            return redirect(url_for('admin_dashboard'))  
        else:
            flash("Invalid admin credentials", "error")
            return redirect(url_for('admin_login'))  

    return render_template('admin_login.html')

# ---------------- ADMIN PANEL ----------------
@app.route('/admin')
def admin_panel():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM contact")
    messages = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin.html', messages=messages)

# ---------------- ADMIN ORDERS ----------------
@app.route('/admin/orders')
def admin_orders():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT orders.*, users.name 
        FROM orders
        JOIN users ON orders.user_id = users.id
        ORDER BY orders.created_at DESC
    """)
    orders = cursor.fetchall()

    for order in orders:
        cursor.execute("""
    SELECT products.name,
       products.image,
       order_items.quantity,
       order_items.price,
       order_items.product_id
FROM order_items
JOIN products ON order_items.product_id = products.id
WHERE order_items.order_id=%s
""", (order['id'],))
        order['order_items'] = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template("admin_orders.html", orders=orders)
# ---------------- UPDATE ORDER STATUS ----------------
@app.route('/admin/update_order_status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    status = request.form.get('status')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE orders SET status=%s WHERE id=%s",
        (status, order_id)
    )

    conn.commit()
    cursor.close()
    conn.close()

    flash("Order status updated successfully!", "success")
    return redirect(url_for('admin_orders'))

# ---------------- ADMIN RETURNS ----------------
@app.route('/admin/returns')
def admin_returns():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT returns.*, users.name, products.name AS product_name
        FROM returns
        JOIN users ON returns.user_id = users.id
        JOIN products ON returns.product_id = products.id
        ORDER BY returns.created_at DESC
    """)

    returns_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("admin_returns.html", returns=returns_list)
@app.route('/admin/update_return/<int:return_id>/<status>')
def update_return_status(return_id, status):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE returns SET status=%s WHERE id=%s",
        (status, return_id)
    )

    conn.commit()

    cursor.close()
    conn.close()

    flash("Return request updated!")

    return redirect(url_for('admin_returns'))

    
# ---------------- ADMIN PRODUCTS ----------------
@app.route("/admin/products")
def admin_products():
    if not session.get('admin_logged_in'):
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("admin_products.html", products=products)

# ---------------- ADMIN ADD PRODUCT ----------------
@app.route("/admin/add_product", methods=["POST"])
def add_product():
    if not session.get('admin_logged_in'):
        return redirect(url_for("admin_login"))

    name = request.form["name"]
    price = request.form["price"]
    description = request.form["description"]
    image = request.form["image"]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO products (name, price, description, image) VALUES (%s,%s,%s,%s)",
        (name, price, description, image),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("admin_products"))

# ---------------- ADMIN DELETE PRODUCT ----------------
@app.route("/admin/delete_product/<int:id>")
def delete_product(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("admin_products"))

# ---------------- ADMIN DASHBOARD ----------------
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) as count FROM orders")
    total_orders = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM products")
    total_products = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM users")
    total_users = cursor.fetchone()['count']

    cursor.close()
    conn.close()
    return render_template(
        "admin_dashboard.html",
        total_orders=total_orders,
        total_products=total_products,
        total_users=total_users
    )
# ---------------- ADMIN CONTACT MESSAGES ----------------

@app.route('/admin_contacts')
def admin_contacts():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM contact ORDER BY id DESC")

    messages = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("admin_contacts.html", messages=messages)
# ---------------- SEEDS ANALYSIS ----------------
@app.route('/seeds_analysis')
def seeds_analysis():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ------------------ Fetch district-wise sales ------------------
    cursor.execute("""
        SELECT district, SUM(order_items.quantity) as total_sold
        FROM orders
        JOIN order_items ON orders.id = order_items.order_id
        GROUP BY district
    """)
    district_data = cursor.fetchall()  # ✅ fetchall() with parentheses

    districts = [row['district'] for row in district_data]
    district_sales = [row['total_sold'] for row in district_data]

    # ------------------ Fetch product-wise sales ------------------
    cursor.execute("""
        SELECT products.name, SUM(order_items.quantity) as total
        FROM order_items
        JOIN products ON order_items.product_id = products.id
        GROUP BY products.name
        ORDER BY total DESC
    """)
    product_data = cursor.fetchall()

    products = [row['name'] for row in product_data]
    product_sales = [row['total'] for row in product_data]

    # ------------------ Prepare ML Clustering ------------------
    # Encode product names
    
    from sklearn.cluster import KMeans

    df = pd.DataFrame(product_data)  # 'name' and 'total'
    if not df.empty:
        df['product_code'] = df['name'].astype('category').cat.codes
        X = df[['product_code', 'total']]

        # KMeans clustering
        kmeans = KMeans(n_clusters=3, random_state=42)
        df['cluster'] = kmeans.fit_predict(X)

        # Example prediction: cluster with highest total sales
        cluster_totals = df.groupby('cluster')['total'].sum()
        top_cluster = cluster_totals.idxmax()
        top_products = df[df['cluster'] == top_cluster]['name'].tolist()
    else:
        df = pd.DataFrame()
        top_products = []

    # ------------------ Prediction ------------------
    prediction = None
    if district_data:
        prediction = max(district_data, key=lambda x: x['total_sold'])['district']

    cursor.close()
    conn.close()

    return render_template(
        "seeds_analysis.html",
        district_data=district_data,
        districts=districts,
        district_sales=district_sales,
        products=products,
        product_sales=product_sales,
        prediction=prediction,
        top_products=top_products,  # top products from cluster
        clustered_df=df.to_dict(orient='records')  # optional for template
    )
# ---------------- STATIC PAGES ----------------
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
