from flask import Flask, render_template, request, flash, redirect, abort, render_template
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

import pymysql

from dynaconf import Dynaconf

config = Dynaconf(settings_file = ["settings.toml"])

app = Flask(__name__)

app.secret_key = config.secret_key

login_manager = LoginManager( app )

login_manager.login_view = '/login'
class User:
    is_authenticated = True
    is_active = True
    is_anonymous = False

    def __init__(self, result):
        self.name = result['Name']
        self.email = result['Email']
        self.address = result['Address']
        self.id = result['ID']
    
    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    connection = connect_db()
    cursor = connection.cursor()
    cursor. execute("SELECT * FROM `User` WHERE `ID` = %s " , (user_id))
    result = cursor.fetchone()
    connection.close()
    if result is None:
        return None
    return User(result)

    

def connect_db():
    conn = pymysql.connect(
        host="db.steamcenter.tech",
        user="vburke",
        password=config.password,
        database="vburke_garlique_gourmet",
        autocommit= True,
        cursorclass= pymysql.cursors.DictCursor
    )
    return conn


@app.route("/")
def index():
    return render_template("homepage.html.jinja")

@app.route("/browse")
def browse():
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM `Product`")
    result = cursor.fetchall()
    connection.close()
    return render_template("browse.html.jinja", products=result)

@app.route("/lunch")
def lunch():
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM `Product`")
    result = cursor.fetchall()
    connection.close()
    return render_template("lunch.html.jinja", products=result)

@app.route("/dinner")
def dinner():
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM `Product`")
    result = cursor.fetchall()
    connection.close()
    return render_template("dinner.html.jinja", products=result)

@app.route("/product/<product_id>")
def product_page(product_id):
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM `Product` WHERE `ID` = %s", ( product_id ))
    result = cursor.fetchone()
    connection.close()
    if result is None:
        abort(404)
    return render_template("product.html.jinja", products=result)

@app.route("/product/<product_id>/add_to_cart", methods=["POST"])
@login_required
def add_to_cart(product_id):
    quantity = request.form["qty"]
    connection = connect_db
    cursor = connection.cursor()
    cursor.execute("""INSERT INTO `Cart` (`Quantity`, `ProductID`, `UserID` VALUES(%s, %s, %s)
    ON DUPLICATE KEY UPDATE
    Quantity + %s
 """, (quantity, product_id, current_user.id, quantity))
    
    result = cursor.fetchone()

    connection.close()
  
    return redirect('/cart')



@app.route('/register', methods= ["POST", "GET"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        address = request.form["address"]
        if password != confirm_password:
            flash("Passwords do not match")
        else:
            connection = connect_db()
            cursor = connection.cursor()
            try:
                cursor.execute("""
                    INSERT INTO `User` (`Name`, `Password`, `Email`, `Address`)
                    VALUES (%s, %s, %s, %s)
                """, (name, password, email, address))
                connection.close()
            except pymysql.err.IntegrityError:
                flash("User with thsat email already exists")
                connection.close()
            else:
                return redirect('/login')
    return render_template('register.html.jinja')

@app.route("/login", methods = ["POST", "GET"])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM `User` WHERE `Email` = %s" , (email) )
        result = cursor.fetchone()
        connection.close()
        if result is None:
            flash("No user found")
        elif password != result["Password"]:
            flash("Incorrect password")
        else:
            login_user(User(result))
            return redirect('/browse')
    return render_template("login.html.jinja")

@app.route("/logout",  methods = ["POST", "GET"])
@login_required
def logout():
    logout_user()
    flash("You Have Been Logged Out! Thanks For Shopping")
    return redirect("/login")

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html.jinja")

@app.route("/cart",  methods = ["POST", "GET"])
@login_required
def cart():
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("""
                   SELECT * FROM `Cart`
                   JOIN `Product` ON `Product`. `ID` = `Cart` . `ProductID`
                   WHERE `UserID` = %s
                   """, (current_user.id))
    results = cursor.fetchall()

    connection.close()
    total = 0
    for item in results:
        total = total + item["Price"] * item["Quantity"]
    
    return render_template("cart.html.jinja", cart=results, total=total)

@app.route("/cart/<product_id>/update_qty",methods=["POST"])
@login_required
def update_cart(product_id):
    new_qty = request.form["qty"]
    connection = connect_db
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE `Cart`
        SET `Quantity`
        WHERE `ProductID` = %s AND `UserID` = %s
    """, (new_qty, product_id, current_user.id) )

    connection.close()

    if len(cart.products) == 0:
        flash("Your cart is empty")


@app.route("/checkout",  methods = ["POST", "GET"])
@login_required
def checkout():
    connection = connect_db
    cursor = connection.cursor()
    cursor.execute("""
                   SELECT * FROM `Cart`
                   JOIN `Product` ON `Product`. `ID` = `Cart` . `ProductID`
                   WHERE `UserID` = %s
                   """, (current_user.id))
    results = cursor.fetchall()
    if request.method == 'POST':
        #create the sale in the database
        cursor.execute("INSERT INTO `Sale` (`UserID`) VALUES (%s)" , (current_user.id, ))
        #store products bought
        sale = cursor.lastrowid
        for item in results:
            cursor.execute( """
                        INSERT INTO `SaleCart` 
                            (`SaleID`, `ProductID`, `Quantity`)
                        VALUES
                           (%s, %s, %s)
                        """, (sale, item['ProductID'], item['Quantity']) )


        #empty cart
        cursor.execute("DELETE FROM `Cart` WHERE `UserID` = %s", (current_user.id,))
        #thank you screen 
        redirect('/thank-you')
    connection.close()
    return render_template("checkout.html.jinja", cart = results)


@app.route("/product/<int:product_id>")
def product(product_id):
    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM Product WHERE id = %s",
        (product_id,)
    )

    product = cursor.fetchone()

    connection.close()

    if not product:
        return "Product not found", 404

    return render_template(
        "product.html.jinja",
        product=product
    )
