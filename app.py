
from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)

# Session security key
app.secret_key = "hospital_project_secret_key_change_this"

# MySQL Database Connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="hospital_db"
    )


# Login required decorator
def login_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first!")
            return redirect(url_for("sign_in"))
        return route_function(*args, **kwargs)
    return wrapper


# Home page
@app.route("/")
def home():
    return redirect(url_for("sign_in"))


# =========================
# SIGN UP
# =========================

@app.route("/sign_up", methods=["GET", "POST"])
def sign_up():

    if request.method == "POST":

        full_name = request.form["full_name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not full_name or not email or not password:
            flash("All fields are required!")
            return redirect(url_for("sign_up"))

        hashed_password = generate_password_hash(password)

        db = get_db_connection()
        cursor = db.cursor()

        try:
            sql = """
                INSERT INTO users (full_name, email, password)
                VALUES (%s, %s, %s)
            """

            cursor.execute(
                sql,
                (full_name, email, hashed_password)
            )

            db.commit()

            flash("Account created successfully! Please login.")
            return redirect(url_for("sign_in"))

        except mysql.connector.IntegrityError:
            flash("This email is already registered!")
            return redirect(url_for("sign_up"))

        finally:
            cursor.close()
            db.close()

    return render_template("sign_up.html")


# =========================
# SIGN IN
# =========================

@app.route("/sign_in", methods=["GET", "POST"])
def sign_in():

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        try:
            sql = "SELECT * FROM users WHERE email = %s"
            cursor.execute(sql, (email,))

            user = cursor.fetchone()

            if user and check_password_hash(
                user["password"], password
            ):

                session.clear()
                session["user_id"] = user["id"]
                session["full_name"] = user["full_name"]

                return redirect(url_for("patient_form"))

            else:
                flash("Invalid email or password!")
                return redirect(url_for("sign_in"))

        finally:
            cursor.close()
            db.close()

    return render_template("sign_in.html")


# =========================
# PATIENT FORM
# =========================

@app.route("/patient_form", methods=["GET", "POST"])
@login_required
def patient_form():

    if request.method == "POST":

        patient_name = request.form["patient_name"].strip()
        age = request.form["age"]
        address = request.form["address"].strip()
        phone = request.form["phone"].strip()
        test_name = request.form["test_name"].strip()
        amount = request.form["amount"]
        visit_date = request.form["visit_date"]

        try:
            age = int(age)
            amount = float(amount)

            if age <= 0 or amount < 0:
                raise ValueError

            db = get_db_connection()
            cursor = db.cursor()

            sql = """
                INSERT INTO patients
                (user_id, patient_name, age, address,
                 phone, test_name, amount, visit_date)

                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                session["user_id"],
                patient_name,
                age,
                address,
                phone,
                test_name,
                amount,
                visit_date
            )

            cursor.execute(sql, values)
            db.commit()

            cursor.close()
            db.close()

            flash("Patient information saved successfully!")
            return redirect(url_for("patient_form"))

        except (ValueError, TypeError):
            flash("Please enter valid age and amount!")
            return redirect(url_for("patient_form"))

    return render_template(
        "patient_form.html",
        full_name=session.get("full_name")
    )


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    flash("You have logged out successfully!")

    return redirect(url_for("sign_in"))


# Run Application
if __name__ == "__main__":
    app.run(debug=True)
