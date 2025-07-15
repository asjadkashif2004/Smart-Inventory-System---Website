from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from flask_mysqldb import MySQL
from flask_dance.contrib.google import make_google_blueprint, google
from werkzeug.utils import secure_filename
import bcrypt
import os

# ------------------ Flask & MySQL Setup ------------------
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PORT'] = 3307
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'mydatabase'

mysql = MySQL(app)

# ------------------ Google OAuth Setup ------------------
google_bp = make_google_blueprint(
    client_id="" #add your clien_id here for google seutup,
    client_secret="" , #add your secret id here
    redirect_url="/login/google/authorized",
    scope=["profile", "email"]
)
app.register_blueprint(google_bp, url_prefix="/login")

# ------------------ WTForms ------------------
class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(), EqualTo('password', message="Passwords must match.")
    ])
    submit = SubmitField("Register")

    def validate_email(self, field):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s", (field.data,))
        user = cursor.fetchone()
        cursor.close()
        if user:
            raise ValidationError("Email already exists.")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

# ------------------ Routes ------------------

@app.route('/')
def front():
    return render_template('front.html')

@app.route('/login/google/authorized')
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("❌ Google login failed.")
        return redirect(url_for("login"))

    user_info = resp.json()
    email = user_info["email"]
    name = user_info.get("name", "No Name")

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                       (name, email, "GOOGLE_LOGIN"))
        mysql.connection.commit()
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

    session['user_id'] = user[0]
    flash("✅ Logged in with Google.")
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                       (name, email, hashed_password))
        mysql.connection.commit()
        cursor.close()

        flash("✅ Registered successfully. Please login.")
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if user and user[3] != "GOOGLE_LOGIN" and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
            session['user_id'] = user[0]
            flash("✅ Logged in successfully.")
            return redirect(url_for('dashboard'))
        else:
            flash("❌ Invalid email or password.")
            return redirect(url_for('login'))

    return render_template('login.html', form=form)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) FROM products WHERE user_id=%s", (user_id,))
    total_products = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT category) FROM products WHERE user_id=%s", (user_id,))
    total_categories = cursor.fetchone()[0]

    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if user[3] == "GOOGLE_LOGIN":
            flash("❌ You are logged in with Google. Password change not allowed.", "danger")
        elif not bcrypt.checkpw(current_password.encode('utf-8'), user[3].encode('utf-8')):
            flash("❌ Current password is incorrect.", "danger")
        elif new_password != confirm_password:
            flash("❌ New passwords do not match.", "danger")
        else:
            hashed_new_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("UPDATE users SET password=%s WHERE id=%s", (hashed_new_pw, user_id))
            mysql.connection.commit()
            flash("✅ Password updated successfully!", "success")

    cursor.close()
    return render_template('dashboard.html', user=user,
                           total_products=total_products,
                           total_categories=total_categories)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("🔓 Logged out successfully.")
    return redirect(url_for('login'))

@app.route('/products')
def products():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM products WHERE user_id=%s", (user_id,))
    products = cursor.fetchall()
    cursor.close()

    return render_template('products.html', products=products)

@app.route('/add_product', methods=['POST'])
def add_product():
    if 'user_id' not in session:
        flash("❌ Please log in to add products.")
        return redirect(url_for('login'))

    name = request.form.get('name', '').strip()
    price = request.form.get('price', '').strip()
    category = request.form.get('category', '').strip()
    stock = request.form.get('stock', '').strip()
    user_id = session['user_id']

    if not name or not price or not category or not stock:
        flash("⚠️ All fields are required.")
        return redirect(url_for('products'))

    try:
        price = float(price)
        stock = int(stock)

        if price < 0 or stock < 0:
            flash("⚠️ Price and stock must be non-negative.")
            return redirect(url_for('products'))

        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO products (name, price, category, stock, user_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, price, category, stock, user_id))
        mysql.connection.commit()
        cursor.close()

        flash("✅ Product added successfully.")
    except ValueError:
        flash("⚠️ Invalid price or stock value.")
    except Exception as e:
        print("Error adding product:", e)
        flash("❌ Error adding product. Try again.")
    return redirect(url_for('products'))

@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM products WHERE id=%s AND user_id=%s", (id, user_id))
    product = cursor.fetchone()

    if not product:
        flash("❌ Product not found.")
        return redirect(url_for('products'))

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        category = request.form['category']
        stock = request.form['stock']

        cursor.execute("UPDATE products SET name=%s, price=%s, category=%s, stock=%s WHERE id=%s AND user_id=%s",
                       (name, price, category, stock, id, user_id))
        mysql.connection.commit()
        flash("✅ Product updated.")
        return redirect(url_for('products'))

    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:id>')
def delete_product(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM products WHERE id=%s AND user_id=%s", (id, user_id))
    mysql.connection.commit()
    cursor.close()

    flash("🗑️ Product deleted.")
    return redirect(url_for('products'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']
    print(f"Message from {name} ({email}): {message}")
    flash("✅ Your message has been sent successfully!", "success")
    return redirect(url_for('contact'))

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    name = request.form['name']
    email = request.form['email']
    user_id = session['user_id']

    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE users SET name=%s, email=%s WHERE id=%s", (name, email, user_id))
    mysql.connection.commit()
    cursor.close()

    flash("✅ Profile updated successfully!")
    return redirect(url_for('dashboard'))

@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if 'profile_image' not in request.files:
        flash("❌ No file uploaded.")
        return redirect(url_for('dashboard'))

    file = request.files['profile_image']
    if file.filename == "":
        flash("❌ No selected file.")
        return redirect(url_for('dashboard'))

    filename = secure_filename(file.filename)
    upload_path = os.path.join('static', 'uploads')
    os.makedirs(upload_path, exist_ok=True)
    file.save(os.path.join(upload_path, filename))

    user_id = session['user_id']
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE users SET profile_image=%s WHERE id=%s", (filename, user_id))
    mysql.connection.commit()
    cursor.close()

    flash("✅ Image uploaded.")
    return redirect(url_for('dashboard'))

# ------------------ Run App ------------------
if __name__ == '__main__':
    app.run(debug=True)
