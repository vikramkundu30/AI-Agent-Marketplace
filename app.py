from flask import Flask, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pymysql
import os

from config import Config
from utils.db import get_db_connection

app = Flask(__name__)
app.config.from_object(Config)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_role'] = user['role']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            return redirect(url_for(f"dashboard_{user['role']}"))
        else:
            flash('Invalid email or password.')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        location = request.form.get('location')
        
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO users (name, email, password_hash, role, location) VALUES (%s, %s, %s, %s, %s)",
                (name, email, hashed_password, role, location)
            )
            conn.commit()
            flash('Registration successful. Please log in.')
            return redirect(url_for('login'))
        except pymysql.err.IntegrityError:
            flash('Email already exists.')
        finally:
            cursor.close()
            conn.close()
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard/customer')
def dashboard_customer():
    if session.get('user_role') != 'customer':
        return redirect(url_for('login'))
        
    query = request.args.get('q', '')
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # Get all products and their manufacturers
    cursor.execute("""
        SELECT p.*, u.name as manufacturer_name 
        FROM products p 
        JOIN users u ON p.manufacturer_id = u.id
    """)
    products = cursor.fetchall()
    
    # Perform AI Search if there is a query
    if query:
        from utils.ai_search import perform_ai_search
        products = perform_ai_search(query, products)
        
    # Attach shopkeeper inventory info for each product
    for product in products:
        cursor.execute("""
            SELECT i.quantity, u.name as shopkeeper_name, u.location, u.id as shopkeeper_id
            FROM inventory i
            JOIN users u ON i.shopkeeper_id = u.id
            WHERE i.product_id = %s AND i.quantity > 0
        """, (product['id'],))
        product['shopkeepers'] = cursor.fetchall()
        
    cursor.close()
    conn.close()
    return render_template('dashboard_customer.html', products=products, query=query)

@app.route('/dashboard/manufacturer')
def dashboard_manufacturer():
    if session.get('user_role') != 'manufacturer':
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM products WHERE manufacturer_id = %s", (session['user_id'],))
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('dashboard_manufacturer.html', products=products)

@app.route('/add_product', methods=['POST'])
def add_product():
    if session.get('user_role') != 'manufacturer':
        return redirect(url_for('login'))
        
    name = request.form.get('name')
    description = request.form.get('description')
    price = request.form.get('price')
    image = request.files.get('image')
    
    image_filename = None
    if image and image.filename != '':
        image_filename = secure_filename(image.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO products (name, description, price, manufacturer_id, image_filename) VALUES (%s, %s, %s, %s, %s)",
        (name, description, price, session['user_id'], image_filename)
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    flash("Product added successfully!")
    return redirect(url_for('dashboard_manufacturer'))

@app.route('/delete_product', methods=['POST'])
def delete_product():
    if session.get('user_role') != 'manufacturer':
        return redirect(url_for('login'))
        
    product_id = request.form.get('product_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    # ON DELETE CASCADE in schema handles inventory removal
    cursor.execute("DELETE FROM products WHERE id = %s AND manufacturer_id = %s", (product_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash("Product deleted successfully.")
    return redirect(url_for('dashboard_manufacturer'))

@app.route('/send_promotion', methods=['POST'])
def send_promotion():
    if session.get('user_role') != 'manufacturer':
        return redirect(url_for('login'))
        
    product_id = request.form.get('product_id')
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # Get product info
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    
    # Get all shopkeepers
    cursor.execute("SELECT email FROM users WHERE role = 'shopkeeper'")
    shopkeepers = cursor.fetchall()
    emails = [s['email'] for s in shopkeepers]
    
    cursor.close()
    conn.close()
    
    if emails and product:
        from utils.email import send_bulk_emails
        subject = f"New Product Opportunity: {product['name']}"
        body = f"""
        <html>
            <body>
                <h2>Partner with us on {product['name']}</h2>
                <p>{product['description']}</p>
                <p>Wholesale Price: <strong>${product['price']}</strong></p>
                <p>Log in to your Nexus AI Market dashboard to add this to your inventory today!</p>
            </body>
        </html>
        """
        success, msg = send_bulk_emails(emails, subject, body)
        if success:
            flash(f"Promotion sent to {len(emails)} shopkeepers!")
        else:
            flash(f"Failed to send promotion: {msg}")
    else:
        flash("No shopkeepers available to promote to.")
        
    return redirect(url_for('dashboard_manufacturer'))

@app.route('/dashboard/shopkeeper')
def dashboard_shopkeeper():
    if session.get('user_role') != 'shopkeeper':
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # Get all products
    cursor.execute("""
        SELECT p.*, u.name as manufacturer_name 
        FROM products p 
        JOIN users u ON p.manufacturer_id = u.id
    """)
    all_products = cursor.fetchall()
    
    # Get shopkeeper's inventory
    cursor.execute("""
        SELECT i.id, i.quantity, p.name as product_name, u.name as manufacturer_name
        FROM inventory i
        JOIN products p ON i.product_id = p.id
        JOIN users u ON p.manufacturer_id = u.id
        WHERE i.shopkeeper_id = %s
    """, (session['user_id'],))
    inventory = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('dashboard_shopkeeper.html', all_products=all_products, inventory=inventory)

@app.route('/add_to_inventory', methods=['POST'])
def add_to_inventory():
    if session.get('user_role') != 'shopkeeper':
        return redirect(url_for('login'))
        
    product_id = request.form.get('product_id')
    quantity = request.form.get('quantity')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if already in inventory
    cursor.execute("SELECT id FROM inventory WHERE shopkeeper_id = %s AND product_id = %s", (session['user_id'], product_id))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("UPDATE inventory SET quantity = quantity + %s WHERE id = %s", (quantity, existing[0]))
    else:
        cursor.execute("INSERT INTO inventory (shopkeeper_id, product_id, quantity) VALUES (%s, %s, %s)", 
                      (session['user_id'], product_id, quantity))
                      
    conn.commit()
    cursor.close()
    conn.close()
    
    flash("Inventory updated!")
    return redirect(url_for('dashboard_shopkeeper'))

@app.route('/update_inventory', methods=['POST'])
def update_inventory():
    if session.get('user_role') != 'shopkeeper':
        return redirect(url_for('login'))
        
    inventory_id = request.form.get('inventory_id')
    quantity = request.form.get('quantity')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if int(quantity) <= 0:
        cursor.execute("DELETE FROM inventory WHERE id = %s AND shopkeeper_id = %s", (inventory_id, session['user_id']))
    else:
        cursor.execute("UPDATE inventory SET quantity = %s WHERE id = %s AND shopkeeper_id = %s", (quantity, inventory_id, session['user_id']))
        
    conn.commit()
    cursor.close()
    conn.close()
    
    flash("Stock level updated.")
    return redirect(url_for('dashboard_shopkeeper'))

@app.route('/remove_inventory', methods=['POST'])
def remove_inventory():
    if session.get('user_role') != 'shopkeeper':
        return redirect(url_for('login'))
        
    inventory_id = request.form.get('inventory_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inventory WHERE id = %s AND shopkeeper_id = %s", (inventory_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash("Item removed from inventory.")
    return redirect(url_for('dashboard_shopkeeper'))

@app.route('/contact/<int:recipient_id>', methods=['GET', 'POST'])
def contact(recipient_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # Get recipient info
    cursor.execute("SELECT id, name, email, role FROM users WHERE id = %s", (recipient_id,))
    recipient = cursor.fetchone()
    
    if not recipient:
        cursor.close()
        conn.close()
        flash("User not found.")
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        subject = request.form.get('subject')
        message = request.form.get('message')
        sender_name = session.get('user_name')
        sender_email = session.get('user_email')
        
        cursor.close()
        conn.close()
        
        # Dispatch email
        from utils.email import send_bulk_emails
        email_body = f"""
        <html>
            <body>
                <h3>New Message from {sender_name} (Nexus AI Market)</h3>
                <p><strong>Reply to:</strong> {sender_email}</p>
                <hr>
                <p>{message.replace(chr(10), '<br>')}</p>
            </body>
        </html>
        """
        success, msg = send_bulk_emails([recipient['email']], subject, email_body)
        
        if success:
            flash(f"Message sent to {recipient['name']} successfully!")
        else:
            flash(f"Failed to send message. SMTP error: {msg}")
            
        # Redirect back to user's dashboard
        return redirect(url_for(f"dashboard_{session.get('user_role')}"))
        
    cursor.close()
    conn.close()
    
    context = request.args.get('context', '')
    return render_template('contact.html', recipient=recipient, context=context)

if __name__ == '__main__':
    app.run(debug=True)
