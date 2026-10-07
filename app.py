from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from functools import wraps

app = Flask(__name__)

app.secret_key = "blood_donor_secret_key"

DATABASE = "database.db"


# ==========================================================
# DATABASE
# ==========================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


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
            address TEXT NOT NULL,
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


# ==========================================================
# ADMIN AUTHENTICATION
# ==========================================================

def admin_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if not session.get("admin"):
            flash("Please login as administrator.", "error")
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


# ==========================================================
# HOME
# ==========================================================

@app.route("/")
def index():

    conn = get_db()

    total_donors = conn.execute(
        "SELECT COUNT(*) FROM donors"
    ).fetchone()[0]

    available_donors = conn.execute(
        "SELECT COUNT(*) FROM donors WHERE available = 1"
    ).fetchone()[0]

    total_requests = conn.execute(
        "SELECT COUNT(*) FROM blood_requests"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "index.html",
        total_donors=total_donors,
        available_donors=available_donors,
        total_requests=total_requests
    )


# ==========================================================
# REGISTER DONOR
# ==========================================================

@app.route("/register-donor", methods=["GET", "POST"])
def register_donor():

    if request.method == "POST":

        name = request.form.get("name")
        age = request.form.get("age")
        gender = request.form.get("gender")
        blood_group = request.form.get("blood_group")
        phone = request.form.get("phone")
        email = request.form.get("email")
        city = request.form.get("city")
        address = request.form.get("address")
        last_donation = request.form.get("last_donation")

        available = 1 if request.form.get("available") else 0

        if not name or not age or not gender:
            flash("Please fill all required fields.", "error")
            return redirect(url_for("register_donor"))

        if not blood_group or not phone:
            flash("Please fill all required fields.", "error")
            return redirect(url_for("register_donor"))

        if not city or not address:
            flash("Please fill all required fields.", "error")
            return redirect(url_for("register_donor"))

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
            available
        ))

        conn.commit()
        conn.close()

        flash("Donor registered successfully!", "success")

        return redirect(url_for("donors"))

    return render_template("register.html")


# ==========================================================
# DONOR LIST
# ==========================================================

@app.route("/donors")
def donors():

    search = request.args.get("search", "").strip()
    blood_group = request.args.get("blood_group", "").strip()
    city = request.args.get("city", "").strip()
    availability = request.args.get("availability", "").strip()

    query = "SELECT * FROM donors WHERE 1=1"

    params = []

    if search:

        query += """
            AND (
                name LIKE ?
                OR phone LIKE ?
                OR city LIKE ?
            )
        """

        value = "%" + search + "%"

        params.extend([
            value,
            value,
            value
        ])

    if blood_group:

        query += " AND blood_group = ?"

        params.append(blood_group)

    if city:

        query += " AND city LIKE ?"

        params.append("%" + city + "%")

    if availability == "available":

        query += " AND available = 1"

    elif availability == "unavailable":

        query += " AND available = 0"

    query += " ORDER BY id DESC"

    conn = get_db()

    donors_list = conn.execute(
        query,
        params
    ).fetchall()

    conn.close()

    return render_template(
        "donors.html",
        donors=donors_list,
        search=search,
        blood_group=blood_group,
        city=city,
        availability=availability
    )


# ==========================================================
# DONOR MAP
# ==========================================================

@app.route("/donor-map")
def donor_map():

    blood_group = request.args.get(
        "blood_group",
        ""
    ).strip()

    city = request.args.get(
        "city",
        ""
    ).strip()

    area = request.args.get(
        "area",
        ""
    ).strip()

    query = """
        SELECT id, name, blood_group, city, address
        FROM donors
        WHERE available = 1
    """

    params = []

    if blood_group:

        query += " AND blood_group = ?"

        params.append(blood_group)

    if city:

        query += " AND city LIKE ?"

        params.append("%" + city + "%")

    if area:

        query += " AND address LIKE ?"

        params.append("%" + area + "%")

    query += " ORDER BY name"

    conn = get_db()

    donors_list = conn.execute(
        query,
        params
    ).fetchall()

    conn.close()

    city_coordinates = {

        "SALEM": [11.6643, 78.1460],

        "ERODE": [11.3410, 77.7172],

        "NAMAKKAL": [11.2189, 78.1674],

        "KOMARAPALAYAM": [11.4450, 77.5830],

        "TIRUCHENGODE": [11.3800, 77.8940],

        "TIRUPUR": [11.1085, 77.3411],

        "COIMBATORE": [11.0168, 76.9558],

        "CHENNAI": [13.0827, 80.2707],

        "MADURAI": [9.9252, 78.1198],

        "TRICHY": [10.7905, 78.7047],

        "TIRUCHIRAPPALLI": [10.7905, 78.7047],

        "THANJAVUR": [10.7870, 79.1378],

        "TANJORE": [10.7870, 79.1378],

        "DINDIGUL": [10.3673, 77.9803],

        "KARUR": [10.9601, 78.0766],

        "HOSUR": [12.7409, 77.8253],

        "BENGALURU": [12.9716, 77.5946]
    }

    map_donors = []

    for donor in donors_list:

        donor_city = donor["city"].upper().strip()

        coordinates = city_coordinates.get(
            donor_city,
            [11.1271, 78.6569]
        )

        map_donors.append({

            "id": donor["id"],

            "name": donor["name"],

            "blood_group": donor["blood_group"],

            "city": donor["city"],

            "address": donor["address"],

            "lat": coordinates[0],

            "lng": coordinates[1]

        })

    return render_template(
        "donor_map.html",
        donors=map_donors,
        blood_group=blood_group,
        city=city,
        area=area
    )


# ==========================================================
# EDIT DONOR
# ==========================================================

@app.route(
    "/edit-donor/<int:donor_id>",
    methods=["GET", "POST"]
)
@admin_required
def edit_donor(donor_id):

    conn = get_db()

    donor = conn.execute(
        "SELECT * FROM donors WHERE id = ?",
        (donor_id,)
    ).fetchone()

    if donor is None:

        conn.close()

        flash(
            "Donor not found.",
            "error"
        )

        return redirect(
            url_for("donors")
        )

    if request.method == "POST":

        name = request.form.get("name")

        age = request.form.get("age")

        gender = request.form.get("gender")

        blood_group = request.form.get("blood_group")

        phone = request.form.get("phone")

        email = request.form.get("email")

        city = request.form.get("city")

        address = request.form.get("address")

        last_donation = request.form.get(
            "last_donation"
        )

        available = (
            1
            if request.form.get("available")
            else 0
        )

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
                last_donation = ?,
                available = ?

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
            available,
            donor_id
        ))

        conn.commit()

        conn.close()

        flash(
            "Donor updated successfully.",
            "success"
        )

        return redirect(
            url_for("donors")
        )

    conn.close()

    return render_template(
        "edit_donor.html",
        donor=donor
    )


# ==========================================================
# DELETE DONOR
# ==========================================================

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

    flash(
        "Donor deleted successfully.",
        "success"
    )

    return redirect(
        url_for("donors")
    )


# ==========================================================
# TOGGLE DONOR AVAILABILITY
# ==========================================================

@app.route(
    "/toggle-availability/<int:donor_id>"
)
@admin_required
def toggle_availability(donor_id):

    conn = get_db()

    donor = conn.execute(
        "SELECT available FROM donors WHERE id = ?",
        (donor_id,)
    ).fetchone()

    if donor:

        new_status = (
            0
            if donor["available"]
            else 1
        )

        conn.execute(
            """
            UPDATE donors

            SET available = ?

            WHERE id = ?
            """,
            (
                new_status,
                donor_id
            )
        )

        conn.commit()

    conn.close()

    return redirect(
        url_for("donors")
    )


# ==========================================================
# LOGIN
# ==========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        username = request.form.get(
            "username"
        )

        password = request.form.get(
            "password"
        )

        if (
            username == "admin"
            and password == "admin123"
        ):

            session["admin"] = True

            flash(
                "Admin login successful.",
                "success"
            )

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid username or password.",
            "error"
        )

    return render_template(
        "login.html"
    )


# ==========================================================
# LOGOUT
# ==========================================================

@app.route("/logout")
def logout():

    session.pop(
        "admin",
        None
    )

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("index")
    )


# ==========================================================
# ADMIN DASHBOARD
# ==========================================================

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
        """
        SELECT COUNT(*)
        FROM blood_requests
        WHERE status = 'Pending'
        """
    ).fetchone()[0]

    approved_requests = conn.execute(
        """
        SELECT COUNT(*)
        FROM blood_requests
        WHERE status = 'Approved'
        """
    ).fetchone()[0]

    rejected_requests = conn.execute(
        """
        SELECT COUNT(*)
        FROM blood_requests
        WHERE status = 'Rejected'
        """
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


# ==========================================================
# ADD BLOOD REQUEST
# ==========================================================

@app.route(
    "/add-request",
    methods=["GET", "POST"]
)
def add_request():

    if request.method == "POST":

        patient_name = request.form.get(
            "patient_name"
        )

        blood_group = request.form.get(
            "blood_group"
        )

        units = request.form.get(
            "units"
        )

        hospital = request.form.get(
            "hospital"
        )

        city = request.form.get(
            "city"
        )

        phone = request.form.get(
            "phone"
        )

        reason = request.form.get(
            "reason"
        )

        if (
            not patient_name
            or not blood_group
            or not units
            or not hospital
            or not city
            or not phone
        ):

            flash(
                "Please fill all required fields.",
                "error"
            )

            return redirect(
                url_for("add_request")
            )

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
                reason
            )

            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_name,
            blood_group,
            units,
            hospital,
            city,
            phone,
            reason
        ))

        conn.commit()

        conn.close()

        flash(
            "Blood request submitted successfully.",
            "success"
        )

        return redirect(
            url_for("requests")
        )

    return render_template(
        "add_request.html"
    )


# ==========================================================
# BLOOD REQUEST LIST
# ==========================================================

@app.route("/requests")
def requests():

    conn = get_db()

    requests_list = conn.execute("""
        SELECT *
        FROM blood_requests
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "requests.html",
        requests=requests_list
    )


# ==========================================================
# APPROVE REQUEST
# ==========================================================

@app.route(
    "/approve-request/<int:request_id>"
)
@admin_required
def approve_request(request_id):

    conn = get_db()

    conn.execute("""
        UPDATE blood_requests

        SET status = 'Approved'

        WHERE id = ?
    """, (
        request_id,
    ))

    conn.commit()

    conn.close()

    flash(
        "Blood request approved.",
        "success"
    )

    return redirect(
        url_for("requests")
    )


# ==========================================================
# REJECT REQUEST
# ==========================================================

@app.route(
    "/reject-request/<int:request_id>"
)
@admin_required
def reject_request(request_id):

    conn = get_db()

    conn.execute("""
        UPDATE blood_requests

        SET status = 'Rejected'

        WHERE id = ?
    """, (
        request_id,
    ))

    conn.commit()

    conn.close()

    flash(
        "Blood request rejected.",
        "success"
    )

    return redirect(
        url_for("requests")
    )


# ==========================================================
# DELETE REQUEST
# ==========================================================

@app.route(
    "/delete-request/<int:request_id>"
)
@admin_required
def delete_request(request_id):

    conn = get_db()

    conn.execute(
        "DELETE FROM blood_requests WHERE id = ?",
        (request_id,)
    )

    conn.commit()

    conn.close()

    flash(
        "Blood request deleted.",
        "success"
    )

    return redirect(
        url_for("requests")
    )


# ==========================================================
# RUN APPLICATION
# ==========================================================

if __name__ == "__main__":

    init_db()

    app.run(
        debug=True
    )