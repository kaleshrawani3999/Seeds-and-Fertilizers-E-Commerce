import smtplib
from email.mime.text import MIMEText
from flask import Flask, render_template, request, redirect, flash, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector

def send_order_confirmation(user_email, total_amount):

    message = f"Your order has been confirmed successfully! Total Amount: ₹{total_amount}. Thank you for shopping with us."

    msg = MIMEText(message)
    msg['Subject'] = "Order Confirmation"
    msg['From'] = "kaleshrawani3999@gmail.com"
    msg['To'] = user_email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login("kaleshrawani3999@gmail.com", "gcvq lwms dyqa iyit")

    server.sendmail("kaleshrawani3999@gmail.com", user_email, msg.as_string())
    server.quit()


app = Flask(__name__)
app.secret_key = 'supersecretkey'

# ---------------- MYSQL CONNECTION ----------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="its.pdv.0410",
    database="indumai"
)
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

        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s,%s,%s)",
            (name, email, hashed_password)
        )
        db.commit()
        cursor.close()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

# ---------------- USER LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()

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
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    cart_count = 0
    if session.get('logged_in'):
        cursor.execute("SELECT SUM(quantity) as total FROM cart WHERE user_id=%s", (session['user_id'],))
        result = cursor.fetchone()
        cart_count = result['total'] if result['total'] else 0

    cursor.close()
    return render_template("products.html", products=products, cart_count=cart_count)

# ---------------- ADD TO CART ----------------
@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):

    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session['user_id']

    cursor = db.cursor()

    # Check if product already in cart
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

    db.commit()
    cursor.close()

    return redirect(url_for('cart_page'))
# ---------------- BUY NOW ----------------
@app.route('/buy_now', methods=['POST'])
def buy_now():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session['user_id']
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))

    cursor = db.cursor()
    cursor.execute("SELECT quantity FROM cart WHERE user_id=%s AND product_id=%s", (user_id, product_id))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("UPDATE cart SET quantity = quantity + %s WHERE user_id=%s AND product_id=%s",
                       (quantity, user_id, product_id))
    else:
        cursor.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (%s,%s,%s)",
                       (user_id, product_id, quantity))
    db.commit()
    cursor.close()
    return redirect(url_for('cart_page'))

# ---------------- CART PAGE ----------------
@app.route('/cart')
def cart_page():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT products.id, products.name, products.price, products.image, cart.quantity
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.user_id = %s
    """, (session['user_id'],))
    cart_items = cursor.fetchall()
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

# ---------------- UPDATE CART ----------------
@app.route('/update_cart', methods=['POST'])
def update_cart():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session['user_id']
    product_id = request.form.get('product_id')
    action = request.form.get('action')

    cursor = db.cursor()

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

    db.commit()
    cursor.close()

    return redirect(url_for('cart_page'))

# ---------------- CHECKOUT ----------------
@app.route('/checkout', methods=['POST'])
def checkout():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session['user_id']
    payment_method = request.form.get('payment_method')

    cursor = db.cursor()

    # Fetch cart items with price
    cursor.execute("""
        SELECT cart.product_id, cart.quantity, products.price
        FROM cart 
        JOIN products ON cart.product_id = products.id
        WHERE cart.user_id=%s
    """, (user_id,))
    items = cursor.fetchall()

    if not items:
        flash("Your cart is empty!", "error")
        return redirect(url_for('cart_page'))

    # Calculate total amount
    total_amount = sum(item[1] * item[2] for item in items)  # quantity * price

    # Save order to DB
    cursor.execute(
        "INSERT INTO orders (user_id, total_amount, status, current_location) VALUES (%s, %s, %s, %s)",
        (user_id, total_amount, 'Pending', 'Processing')
    )
    order_id = cursor.lastrowid

    # Insert order items
    for item in items:
        cursor.execute(
            "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s,%s,%s,%s)",
            (order_id, item[0], item[1], item[2])
        )

    # Clear cart
    cursor.execute("DELETE FROM cart WHERE user_id=%s", (user_id,))
    db.commit()
    cursor.close()

    flash(f"Order placed successfully! Total amount: ₹{total_amount}", "success")
    return redirect(url_for('orders'))

# ---------------- ORDERS ----------------
@app.route('/orders')
def orders():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = db.cursor(dictionary=True)

    # Get all orders for the user
    cursor.execute("""
        SELECT * FROM orders
        WHERE user_id=%s
        ORDER BY created_at DESC
    """, (user_id,))
    orders_list = cursor.fetchall()

    # Get items for each order
    for order in orders_list:
        cursor.execute("""
            SELECT products.name, order_items.quantity, order_items.price
            FROM order_items
            JOIN products ON order_items.product_id = products.id
            WHERE order_items.order_id=%s
        """, (order['id'],))
        order['items'] = cursor.fetchall()

    cursor.close()
    return render_template('orders.html', orders=orders_list)

# ---------------- CONTACT ----------------
@app.route('/contact', methods=['GET','POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO contact (name, email, message) VALUES (%s, %s, %s)",
            (name, email, message)
        )
        db.commit()
        cursor.close()

        flash("Message received successfully!", "success")
        return redirect(url_for('contact'))
    return render_template('contact.html')

# ---------------- STATIC PAGES ----------------
@app.route("/")
def home():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products LIMIT 8")
    products = cursor.fetchall()
    cart_count = 0
    if session.get('logged_in'):
        cursor.execute("SELECT SUM(quantity) as total FROM cart WHERE user_id=%s", (session['user_id'],))
        result = cursor.fetchone()
        cart_count = result['total'] if result['total'] else 0
    return render_template("index.html", products=products, cart_count=cart_count)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/gallery")
def gallery():
    return render_template("gallery.html")

@app.route("/blog")
def blog():
    return render_template("blog.html")



# ---------------- ADMIN LOGIN ----------------
@app.route('/admin_login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s AND is_admin=1", (email,))
        admin = cursor.fetchone()
        cursor.close()

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

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM contact")
    messages = cursor.fetchall()
    return render_template('admin.html', messages=messages)
# ---------------- DELETE CONTACT MESSAGE ----------------
@app.route('/admin/delete/<int:msg_id>', methods=['POST'])
def delete_message(msg_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    cursor = db.cursor()
    cursor.execute("DELETE FROM contact WHERE id=%s", (msg_id,))
    db.commit()
    cursor.close()

    flash("Message deleted successfully!", "success")
    return redirect(url_for('admin_panel'))
# ---------------- ADMIN VIEW ORDERS ----------------
@app.route('/admin/orders')
def admin_orders():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    cursor = db.cursor(dictionary=True)

    # Get all orders with user name
    cursor.execute("""
        SELECT orders.*, users.name 
        FROM orders
        JOIN users ON orders.user_id = users.id
        ORDER BY orders.created_at DESC
    """)
    orders = cursor.fetchall()

    # Get items for each order
    for order in orders:
        cursor.execute("""
            SELECT products.name, order_items.quantity, order_items.price
            FROM order_items
            JOIN products ON order_items.product_id = products.id
            WHERE order_items.order_id=%s
        """, (order['id'],))
        order['order_items'] = cursor.fetchall()

    cursor.close()
    return render_template("admin_orders.html", orders=orders)
# ---------------- ADMIN UPDATE ORDER STATUS ----------------
@app.route('/admin/update_status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    new_status = request.form.get('status')

    cursor = db.cursor()
    cursor.execute(
        "UPDATE orders SET status=%s WHERE id=%s",
        (new_status, order_id)
    )
    db.commit()
    cursor.close()

    flash("Order status updated successfully!", "success")
    return redirect(url_for('admin_orders'))
# ---------------- ADMIN PRODUCTS----------------
@app.route("/admin/products")
def admin_products():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    conn.close()

    return render_template("admin_products.html", products=products)
# ---------------- ADMIN ADD PRODUCTS ----------------
@app.route("/admin/add_product", methods=["POST"])
def add_product():
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
    conn.close()

    return redirect(url_for("admin_products"))

# ---------------- ADMIN DELETE PRODUCTS----------------
@app.route("/admin/delete_product/<int:id>")
def delete_product(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM products WHERE id=%s", (id,))

    conn.commit()
    conn.close()

    return redirect(url_for("admin_products"))
# ---------------- ADMIN DASHBOARD ----------------

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) as count FROM orders")
    total_orders = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM products")
    total_products = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM users")
    total_users = cursor.fetchone()['count']

    cursor.close()

    return render_template(
        "admin_dashboard.html",
        total_orders=total_orders,
        total_products=total_products,
        total_users=total_users
    )

if __name__ == '__main__':

    app.run(host="0.0.0.0", port=5000, debug=True)

