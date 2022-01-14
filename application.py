import os
from cs50 import SQL
from flask import Flask, redirect, render_template, request, session, flash
from flask_session import Session
from functools import wraps

from werkzeug.security import check_password_hash, generate_password_hash

# From CS50 week 9 notes
app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

uri = os.getenv("DATABASE_URL")
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://")
systemdb = SQL(uri)

units = ["kJ", "Calories"]

# https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/ and CS50 Finance
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("userid") is None:
            flash("Login required.")
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def kjtocal(kj):
    try:
        cal = round(kj / 4.184)
        return cal

    except:
        return

app.jinja_env.filters["kjtocal"] = kjtocal


def totalling(arraydict, column):
    total = 0

    for item in arraydict:
        total += item[column]

    return total

app.jinja_env.filters["totalling"] = totalling


def caltokj(cal):
    kj = round(cal * 4.184)
    return kj


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        # checking if all the fields are filled in
        if not request.form.get("username") or not request.form.get("password"):
            return render_template("login.html", alert="Must enter both fields")

        check = systemdb.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # checking if inputs match the accounts in the database
        if len(check) == 1 and check_password_hash(check[0]["password"], request.form.get("password")) == True:
            session["userid"] = check[0]["userid"]
            flash("Login successful!")
            return redirect("/")

        return render_template("login.html", alert="Incorrect username or password")

    else:
        return render_template("login.html")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/logbook", methods=["GET", "POST"])
@login_required
def foodlogbook():
    meals = ["Other", "Snack", "Dinner", "Lunch", "Breakfast", ""]

    # Retrieve user info
    dates = systemdb.execute("SELECT DISTINCT(date) FROM fooddiary WHERE userid = ? ORDER BY date", session["userid"])
    info = {}

    for date in dates:
        tempvar = systemdb.execute("SELECT * FROM fooddiary WHERE userid = ? AND date = ? ORDER BY meal = 'Other', meal = 'Snack', meal = 'Dinner', meal = 'Lunch', meal = 'Breakfast'",
            session["userid"], date["date"])
        info[date["date"]] = tempvar

    # Add new logs
    if request.method == "POST":

        if request.form['btn'] == 'add':
            if not request.form.get("energycount") or not request.form.get("units"):
                return render_template("logbook.html", alert="Must enter energy count and its units.", info=info)

            if request.form.get("meal") not in meals:
                return render_template("logbook.html", alert="Not a valid choice for meals.", info=info)

            if request.form.get("units") not in units:
                return render_template("logbook.html", alert="Not a valid choice for units.", info=info)

            if request.form.get("units") == "kJ":
                kJ = int(request.form.get("energycount"))

            else:
                kJ = caltokj(int(request.form.get("energycount")))

            if not request.form.get("date"):
                systemdb.execute("INSERT INTO fooddiary (userid, food, meal, kJenergy) VALUES (?,?,?,?)",
                    session["userid"], request.form.get("foodname"), request.form.get("meal"), kJ)

            else:
                systemdb.execute("INSERT INTO fooddiary (userid, food, meal, kJenergy, date) VALUES (?,?,?,?,?)",
                    session["userid"], request.form.get("foodname"), request.form.get("meal"), kJ, request.form.get("date"))

            flash("New log added!")
            return redirect("/logbook")

    else:
        return render_template("logbook.html", info=info)


@app.route("/kjcalc", methods=["GET","POST"])
@login_required
def kjcalc():

    ingredients = systemdb.execute("SELECT name FROM fooddata")
    prevrecipes = systemdb.execute("SELECT * FROM recipe WHERE userid = ?", session["userid"])

    if request.method == "POST":

        if request.form['function'] == 'newrecipe':

            if not request.form.get("recipename"):
                return render_template("kjcalc1.html", past=prevrecipes, alert="Must enter a recipe name.")

            check = systemdb.execute("SELECT * FROM recipe WHERE userid = ? AND name = ?", session["userid"], request.form.get("recipename"))

            if check:
                return render_template("kjcalc1.html", past=prevrecipes, alert="Recipe already exists.")

            # create new recipe
            session.pop('recipeid', None)
            session["recipeid"] = systemdb.execute("INSERT INTO recipe (name, userid) VALUES (?, ?)", request.form.get("recipename"), session["userid"])
            flash("Recipe successfully saved!")
            return render_template("kjcalc2.html", data=ingredients, recipe=request.form.get("recipename"))

        if request.form['function'] == 'revisit':
            check = systemdb.execute("SELECT * FROM recipe WHERE name = ? AND userid = ?", request.form.get("oldrecipes"), session["userid"])
            if not check:
                return render_template("kjcalc1.html", alert="Invalid recipe.", past=prevrecipes)

            session["recipeid"] = check[0]["recipeid"]
            curr = systemdb.execute("SELECT * FROM ingredients WHERE userid = ? AND recipeid = ?", session["userid"], session["recipeid"])
            recipe = systemdb.execute("SELECT * FROM recipe WHERE userid = ? AND recipeid = ?", session["userid"], session["recipeid"])
            return render_template("kjcalc2.html", curr=curr, data=ingredients, recipe=recipe[0]["name"])

        if request.form['function'] == 'redirectto1':
            session["recipeid"] = None
            return redirect("/kjcalc")

        recipe = systemdb.execute("SELECT * FROM recipe WHERE userid = ? AND recipeid = ?", session["userid"], session["recipeid"])

        if request.form['function'] == 'add':
            curr = systemdb.execute("SELECT * FROM ingredients WHERE userid = ? AND recipeid = ?", session["userid"], session["recipeid"])

            if not request.form.get("ingredient") or not request.form.get("quantity"):
                return render_template("kjcalc2.html", data=ingredients, curr=curr, alert="Must fill up both fields.", recipe=recipe[0]["name"])

            try:
                float(request.form.get("quantity"))

            except:
                return render_template("kjcalc2.html", data=ingredients, curr=curr, alert="Quantity must be numeric.", recipe=recipe[0]["name"])

            # figure out what ingredient, retrieve it's kj count, divide it by 100 and multiply it by the size and add it to db
            kJ100 = systemdb.execute("SELECT kJ FROM fooddata WHERE name = ?", request.form.get("ingredient"))
            kJsingle = round(kJ100[0]["kJ"] / 100 * float(request.form.get("quantity")))

            systemdb.execute("INSERT INTO ingredients (userid, recipeid, ingredient, kJ100, quantity, kJ) VALUES (?,?,?,?,?,?)",
                session["userid"], session["recipeid"], request.form.get("ingredient"), kJ100[0]["kJ"], request.form.get("quantity"), kJsingle)

            curr = systemdb.execute("SELECT * FROM ingredients WHERE userid = ? AND recipeid = ?", session["userid"], session["recipeid"])

            flash("Ingredient added.")
            return render_template("kjcalc2.html", curr=curr, data=ingredients, recipe=recipe[0]["name"])

        if request.form['function'] == 'addspecial':
            curr = systemdb.execute("SELECT * FROM ingredients WHERE userid = ? AND recipeid = ?", session["userid"], session["recipeid"])

            if not request.form.get("totalkJ") and not request.form.get("kJ100"):
                return render_template("kjcalc2.html", alert="Must enter energy count for the amount used or the ingredient in 100g and its units.", curr=curr, data=ingredients, recipe=recipe[0]["name"])

            if request.form.get("kJ100") and not request.form.get("quantity"):
                return render_template("kjcalc2.html", alert="Must enter energy count per 100 and the quantity used.", curr=curr, data=ingredients, recipe=recipe[0]["name"])

            if not request.form.get("units") or request.form.get("units") not in units:
                return render_template("kjcalc2.html", alert="Must enter units or not a valid choice for units.", curr=curr, data=ingredients, recipe=recipe[0]["name"])

            try:
                float(request.form.get("quantity"))

            except:
                return render_template("kjcalc2.html", data=ingredients, curr=curr, alert="Quantity must be numeric.", recipe=recipe[0]["name"])

            if request.form.get("kJ100"):
                if request.form.get("units") == "kJ":
                    kJ = int(request.form.get("kJ100"))

                else:
                    kJ = caltokj(int(request.form.get("kJ100")))

                total = round(kJ/100 * int(request.form.get("quantity")))

                systemdb.execute("INSERT INTO ingredients (userid, recipeid, ingredient, kJ100, quantity, kJ) VALUES (?,?,?,?,?,?)",
                    session["userid"], session["recipeid"], request.form.get("name"), kJ, request.form.get("quantity"), total)

            else:
                if request.form.get("units") == "kJ":
                    kJ = int(request.form.get("totalkJ"))

                else:
                    kJ = caltokj(int(request.form.get("totalkJ")))

                systemdb.execute("INSERT INTO ingredients (userid, recipeid, ingredient, kJ) VALUES (?,?,?,?)",
                    session["userid"], session["recipeid"], request.form.get("name"), kJ)

            curr = systemdb.execute("SELECT * FROM ingredients WHERE userid = ? AND recipeid = ?", session["userid"], session["recipeid"])

            flash("Ingredient added.")
            return render_template("kjcalc2.html", curr=curr, data=ingredients, recipe=recipe[0]["name"])

        if request.form['function'] == 'serving':
            curr = systemdb.execute("SELECT * FROM ingredients WHERE userid = ? AND recipeid = ?", session["userid"], session["recipeid"])

            serveinfo = {}

            if not request.form.get("servings"):
                return render_template("kjcalc2.html", curr=curr, data=ingredients, alert="Must fill in the number of servings.", recipe=recipe[0]["name"])

            serveinfo["serves"] = request.form.get("servings")

            if not request.form.get("totalkJ"):
                if not request.form.get("totalcal"):
                    return render_template("kjcalc2.html", curr=curr, data=ingredients, alert="Must fill in the energy count in kJ or calories.", recipe=recipe[0]["name"])

                serveinfo["totalkJ"] = caltokj(int(request.form.get("totalcal")))

            else:
                if request.form.get("totalcal"):
                    return render_template("kjcalc2.html", curr=curr, data=ingredients, alert="Only fill in energy count in kJ OR calories.", recipe=recipe[0]["name"])

                serveinfo["totalkJ"] = request.form.get("totalkJ")

            return render_template("kjcalc2.html", curr=curr, data=ingredients, serveinfo=serveinfo, recipe=recipe[0]["name"])


    else:
        prevrecipes = systemdb.execute("SELECT * FROM recipe WHERE userid = ?", session["userid"])
        return render_template("kjcalc1.html", past=prevrecipes)

@app.route("/recipes", methods=["GET", "POST"])
@login_required
def recipes():
    if request.method == "POST":
        systemdb.execute("DELETE FROM recipe WHERE userid = ? AND recipeid = ?", session["userid"], request.form.get("recipeid"))
        systemdb.execute("DELETE FROM ingredients WHERE userid = ? AND recipeid = ?", session["userid"], request.form.get("recipeid"))
        flash("Recipe deleted")
        return redirect("/recipes")

    else:
        names = systemdb.execute("SELECT * FROM recipe WHERE userid = ?", session["userid"])
        return render_template("recipes.html", names = names)

@app.route("/deleteingredient", methods=["GET","POST"])
@login_required
def deleteingredient():

    systemdb.execute("DELETE FROM ingredients WHERE userid = ? AND ingredientid = ?", session["userid"], request.form.get("ingredientid"))
    ingredients = systemdb.execute("SELECT name FROM fooddata")
    curr = systemdb.execute("SELECT * FROM ingredients WHERE userid = ? AND recipeid = ?", session["userid"], session["recipeid"])
    recipe = systemdb.execute("SELECT * FROM recipe WHERE userid = ? AND recipeid = ?", session["userid"], session["recipeid"])

    return render_template("kjcalc2.html", curr=curr, data=ingredients, recipe=recipe[0]["name"])


@app.route("/deletelog", methods=["GET","POST"])
@login_required
def deletelog():

    systemdb.execute("DELETE FROM fooddiary WHERE userid = ? AND logid = ?", session["userid"], request.form.get("logid"))
    flash("Log successfully deleted.")
    return redirect("/logbook")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        # checking if all the fields are filled in
        if not request.form.get("username") or not request.form.get("password"):
            return render_template("register.html", alert="Must enter both fields")

        # checking if the username already exists
        rows = systemdb.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        if len(rows) != 0:
            return render_template("register.html", alert="Username already taken")

        # adding user data to the table
        else:
            systemdb.execute("INSERT INTO users (username, password) VALUES (?,?)", request.form.get(
                "username"), generate_password_hash(request.form.get("password")))

            flash("Registration successful!")
            return redirect("/login")

    else:
        return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    session["userid"] = None
    flash("Logout successful!")
    return redirect("/")


@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changepassword():
    """Allow the user to change their password"""

    if request.method == "POST":

        if not request.form.get("oldpass") or not request.form.get("newpass"):
            return render_template("changepassword.html", alert="Must fill both fields")

        # Query database for user details
        rows = systemdb.execute("SELECT * FROM users WHERE userid = ?", session["userid"])

        # Check if the password is correct
        if not check_password_hash(rows[0]["password"], request.form.get("oldpass")):
            return render_template("changepassword.html", alert="Invalid old password.")

        systemdb.execute("UPDATE users SET password = ? WHERE userid = ?", generate_password_hash(
            request.form.get("newpass")), session["userid"])

        flash("Password successfully changed!")
        return redirect("/")

    else:
        return render_template("changepassword.html")