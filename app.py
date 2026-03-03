from flask import Flask, render_template, request, redirect, session
import mysql.connector

app = Flask(__name__)
app.secret_key = "inventory_secret_key"

# ---------------- DATABASE CONNECTION ----------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",          # Default XAMPP password
    database="inventorydb"
)

cursor = db.cursor(dictionary=True)

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        cursor.execute(
            "SELECT * FROM admin WHERE username=%s AND password=%s",
            (username, password)
        )
        user = cursor.fetchone()

        if user:
            session["admin"] = username
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Invalid Username or Password")

    return render_template("login.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect("/")

    cursor.execute("SELECT COUNT(*) AS total_products FROM products")
    total_products = cursor.fetchone()["total_products"]

    cursor.execute("SELECT SUM(quantity) AS total_quantity FROM products")
    total_quantity = cursor.fetchone()["total_quantity"] or 0

    cursor.execute("SELECT COUNT(*) AS low_stock FROM products WHERE quantity < 5")
    low_stock = cursor.fetchone()["low_stock"]

    cursor.execute("SELECT SUM(quantity * price) AS total_value FROM products")
    total_value = cursor.fetchone()["total_value"] or 0

    return render_template(
        "dashboard.html",
        total_products=total_products,
        total_quantity=total_quantity,
        low_stock=low_stock,
        total_value=total_value
    )


# ---------------- VIEW PRODUCTS + SEARCH ----------------
@app.route("/products")
def products():
    if "admin" not in session:
        return redirect("/")

    search = request.args.get("search")

    if search:
        cursor.execute(
            "SELECT * FROM products WHERE product_name LIKE %s OR category LIKE %s",
            ('%' + search + '%', '%' + search + '%')
        )
    else:
        cursor.execute("SELECT * FROM products")

    products = cursor.fetchall()

    return render_template("products.html", products=products)


# ---------------- ADD PRODUCT ----------------
@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    if "admin" not in session:
        return redirect("/")

    if request.method == "POST":
        name = request.form["product_name"]
        category = request.form["category"]
        quantity = request.form["quantity"]
        price = request.form["price"]

        cursor.execute(
            "INSERT INTO products (product_name, category, quantity, price) VALUES (%s,%s,%s,%s)",
            (name, category, quantity, price)
        )
        db.commit()

        return redirect("/products")

    return render_template("add_product.html")


# ---------------- EDIT PRODUCT ----------------
@app.route("/edit_product/<int:id>", methods=["GET", "POST"])
def edit_product(id):
    if "admin" not in session:
        return redirect("/")

    if request.method == "POST":
        name = request.form["product_name"]
        category = request.form["category"]
        quantity = request.form["quantity"]
        price = request.form["price"]

        cursor.execute("""
            UPDATE products
            SET product_name=%s,
                category=%s,
                quantity=%s,
                price=%s
            WHERE id=%s
        """, (name, category, quantity, price, id))

        db.commit()
        return redirect("/products")

    cursor.execute("SELECT * FROM products WHERE id=%s", (id,))
    product = cursor.fetchone()

    return render_template("edit_product.html", product=product)


# ---------------- DELETE PRODUCT ----------------
@app.route("/delete_product/<int:id>")
def delete_product(id):
    if "admin" not in session:
        return redirect("/")

    cursor.execute("DELETE FROM products WHERE id=%s", (id,))
    db.commit()

    return redirect("/products")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")


# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run(debug=True)