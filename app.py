from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = "blood_donor_secret_key"

DATABASE = "database.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_db():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS donors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            blood_group TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            city TEXT NOT NULL,
            address TEXT,
            last_donation TEXT,
            available INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blood_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            blood_group TEXT NOT NULL,
            units INTEGER NOT NULL,
            hospital TEXT NOT NULL,
            city TEXT NOT NULL,
            phone TEXT NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# ADMIN LOGIN DECORATOR
# =========================================================

def admin_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "admin" not in session:
            flash("Please login as administrator.", "warning")
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    conn = get_db()

    donor_count = conn.execute(
        "SELECT COUNT(*) FROM donors"
    ).fetchone()[0]

    available_count = conn.execute(
        "SELECT COUNT(*) FROM donors WHERE available = 1"
    ).fetchone()[0]

    request_count = conn.execute(
        "SELECT COUNT(*) FROM blood_requests"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "index.html",
        donor_count=donor_count,
        available_count=available_count,
        request_count=request_count
    )


# =========================================================
# REGISTER DONOR
# =========================================================

@app.route("/register-donor", methods=["GET", "POST"])
def register_donor():

    if request.method == "POST":

        name = request.form["name"]
        age = request.form["age"]
        gender = request.form["gender"]
        blood_group = request.form["blood_group"]
        phone = request.form["phone"]
        email = request.form["email"]
        city = request.form["city"]
        address = request.form["address"]
        last_donation = request.form["last_donation"]

        conn = get_db()

        conn.execute("""
            INSERT INTO donors
            (
                name,
                age,
                gender,
                blood_group,
                phone,
                email,
                city,
                address,
                last_donation,
                available
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            age,
            gender,
            blood_group,
            phone,
            email,
            city,
            address,
            last_donation,
            1
        ))

        conn.commit()
        conn.close()

        flash("Donor registered successfully!", "success")

        return redirect(url_for("donors"))

    return render_template("register.html")


# =========================================================
# DONOR LIST + SEARCH + LOCATION FILTER
# =========================================================

@app.route("/donors")
def donors():

    search = request.args.get("search", "").strip()
    blood_group = request.args.get("blood_group", "").strip()
    city = request.args.get("city", "").strip()
    availability = request.args.get("availability", "").strip()

    conn = get_db()

    query = "SELECT * FROM donors WHERE 1=1"
    params = []

    # Search name / phone / city / address
    if search:

        query += """
            AND (
                name LIKE ?
                OR phone LIKE ?
                OR city LIKE ?
                OR address LIKE ?
            )
        """

        search_value = f"%{search}%"

        params.extend([
            search_value,
            search_value,
            search_value,
            search_value
        ])

    # Blood group filter
    if blood_group:

        query += " AND blood_group = ?"
        params.append(blood_group)

    # City filter
    if city:

        query += " AND city LIKE ?"
        params.append(f"%{city}%")

    # Availability filter
    if availability == "available":

        query += " AND available = 1"

    elif availability == "unavailable":

        query += " AND available = 0"

    query += " ORDER BY id DESC"

    donors_list = conn.execute(
        query,
        params
    ).fetchall()

    # Get all locations
    cities = conn.execute("""
        SELECT DISTINCT city
        FROM donors
        WHERE city IS NOT NULL
        AND city != ''
        ORDER BY city
    """).fetchall()

    conn.close()

    return render_template(
        "donors.html",
        donors=donors_list,
        cities=cities,
        search=search,
        selected_blood_group=blood_group,
        selected_city=city,
        selected_availability=availability
    )


# =========================================================
# EDIT DONOR
# =========================================================

@app.route("/edit-donor/<int:donor_id>", methods=["GET", "POST"])
@admin_required
def edit_donor(donor_id):

    conn = get_db()

    donor = conn.execute(
        "SELECT * FROM donors WHERE id = ?",
        (donor_id,)
    ).fetchone()

    if not donor:

        conn.close()

        flash("Donor not found.", "danger")

        return redirect(url_for("donors"))

    if request.method == "POST":

        name = request.form["name"]
        age = request.form["age"]
        gender = request.form["gender"]
        blood_group = request.form["blood_group"]
        phone = request.form["phone"]
        email = request.form["email"]
        city = request.form["city"]
        address = request.form["address"]
        last_donation = request.form["last_donation"]

        conn.execute("""
            UPDATE donors
            SET
                name = ?,
                age = ?,
                gender = ?,
                blood_group = ?,
                phone = ?,
                email = ?,
                city = ?,
                address = ?,
                last_donation = ?
            WHERE id = ?
        """, (
            name,
            age,
            gender,
            blood_group,
            phone,
            email,
            city,
            address,
            last_donation,
            donor_id
        ))

        conn.commit()
        conn.close()

        flash("Donor details updated successfully!", "success")

        return redirect(url_for("donors"))

    conn.close()

    return render_template(
        "edit_donor.html",
        donor=donor
    )


# =========================================================
# DELETE DONOR
# =========================================================

@app.route("/delete-donor/<int:donor_id>")
@admin_required
def delete_donor(donor_id):

    conn = get_db()

    conn.execute(
        "DELETE FROM donors WHERE id = ?",
        (donor_id,)
    )

    conn.commit()
    conn.close()

    flash("Donor deleted successfully.", "success")

    return redirect(url_for("donors"))


# =========================================================
# TOGGLE DONOR AVAILABILITY
# =========================================================

@app.route("/toggle-availability/<int:donor_id>")
@admin_required
def toggle_availability(donor_id):

    conn = get_db()

    donor = conn.execute(
        "SELECT available FROM donors WHERE id = ?",
        (donor_id,)
    ).fetchone()

    if donor:

        new_status = 0 if donor["available"] else 1

        conn.execute(
            """
            UPDATE donors
            SET available = ?
            WHERE id = ?
            """,
            (new_status, donor_id)
        )

        conn.commit()

    conn.close()

    return redirect(url_for("donors"))


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":

            session["admin"] = username

            flash("Login successful!", "success")

            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.pop("admin", None)

    flash("Logged out successfully.", "success")

    return redirect(url_for("index"))


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/dashboard")
@admin_required
def dashboard():

    conn = get_db()

    total_donors = conn.execute(
        "SELECT COUNT(*) FROM donors"
    ).fetchone()[0]

    available_donors = conn.execute(
        "SELECT COUNT(*) FROM donors WHERE available = 1"
    ).fetchone()[0]

    unavailable_donors = conn.execute(
        "SELECT COUNT(*) FROM donors WHERE available = 0"
    ).fetchone()[0]

    total_requests = conn.execute(
        "SELECT COUNT(*) FROM blood_requests"
    ).fetchone()[0]

    pending_requests = conn.execute(
        "SELECT COUNT(*) FROM blood_requests WHERE status = 'Pending'"
    ).fetchone()[0]

    approved_requests = conn.execute(
        "SELECT COUNT(*) FROM blood_requests WHERE status = 'Approved'"
    ).fetchone()[0]

    rejected_requests = conn.execute(
        "SELECT COUNT(*) FROM blood_requests WHERE status = 'Rejected'"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total_donors=total_donors,
        available_donors=available_donors,
        unavailable_donors=unavailable_donors,
        total_requests=total_requests,
        pending_requests=pending_requests,
        approved_requests=approved_requests,
        rejected_requests=rejected_requests
    )


# =========================================================
# ADD BLOOD REQUEST
# =========================================================

@app.route("/add-request", methods=["GET", "POST"])
def add_request():

    if request.method == "POST":

        patient_name = request.form["patient_name"]
        blood_group = request.form["blood_group"]
        units = request.form["units"]
        hospital = request.form["hospital"]
        city = request.form["city"]
        phone = request.form["phone"]
        reason = request.form["reason"]

        conn = get_db()

        conn.execute("""
            INSERT INTO blood_requests
            (
                patient_name,
                blood_group,
                units,
                hospital,
                city,
                phone,
                reason,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_name,
            blood_group,
            units,
            hospital,
            city,
            phone,
            reason,
            "Pending"
        ))

        conn.commit()
        conn.close()

        flash("Blood request submitted successfully!", "success")

        return redirect(url_for("requests"))

    return render_template("add_request.html")


# =========================================================
# VIEW BLOOD REQUESTS
# =========================================================

@app.route("/requests")
@admin_required
def requests():

    conn = get_db()

    blood_requests = conn.execute("""
        SELECT *
        FROM blood_requests
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "requests.html",
        requests=blood_requests
    )


# =========================================================
# APPROVE REQUEST
# =========================================================

@app.route("/approve-request/<int:request_id>")
@admin_required
def approve_request(request_id):

    conn = get_db()

    conn.execute("""
        UPDATE blood_requests
        SET status = 'Approved'
        WHERE id = ?
    """, (request_id,))

    conn.commit()
    conn.close()

    flash("Blood request approved.", "success")

    return redirect(url_for("requests"))


# =========================================================
# REJECT REQUEST
# =========================================================

@app.route("/reject-request/<int:request_id>")
@admin_required
def reject_request(request_id):

    conn = get_db()

    conn.execute("""
        UPDATE blood_requests
        SET status = 'Rejected'
        WHERE id = ?
    """, (request_id,))

    conn.commit()
    conn.close()

    flash("Blood request rejected.", "warning")

    return redirect(url_for("requests"))


# =========================================================
# DELETE REQUEST
# =========================================================

@app.route("/delete-request/<int:request_id>")
@admin_required
def delete_request(request_id):

    conn = get_db()

    conn.execute(
        "DELETE FROM blood_requests WHERE id = ?",
        (request_id,)
    )

    conn.commit()
    conn.close()

    flash("Blood request deleted.", "success")

    return redirect(url_for("requests"))


# =========================================================
# START DATABASE
# =========================================================

init_db()


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)