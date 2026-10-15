from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)

from werkzeug.security import (
    generate_password_hash, check_password_hash
)

from database import get_db_connection, init_db

app = Flask(__name__)

# Used to protect session data.
# Change this value before deploying the application.
app.secret_key = "change-this-citycare-secret-key"


@app.route("/")
def index():
    return render_template("index.html")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please fill in all fields.", "error")
            return redirect(url_for("register"))

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
            return redirect(url_for("register"))

        conn = get_db_connection()

        try:
            conn.execute("""
                INSERT INTO users (name, email, password, role)
                VALUES (?, ?, ?, 'user')
            """, (
                name,
                email,
                generate_password_hash(password)
            ))

            conn.commit()

        except Exception:
            flash("This email may already be registered.", "error")
            return redirect(url_for("register"))

        finally:
            conn.close()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect(url_for("admin"))

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out successfully.", "success")
    return redirect(url_for("index"))


# ---------------- USER DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") == "admin":
        return redirect(url_for("admin"))

    conn = get_db_connection()

    complaints = conn.execute("""
        SELECT * FROM complaints
        WHERE user_id = ?
        ORDER BY id DESC
    """, (session["user_id"],)).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        complaints=complaints
    )


# ---------------- NEW COMPLAINT ----------------

@app.route("/new-complaint", methods=["GET", "POST"])
def new_complaint():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") == "admin":
        return redirect(url_for("admin"))

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        category = request.form.get("category", "").strip()
        location = request.form.get("location", "").strip()
        description = request.form.get("description", "").strip()

        allowed_categories = [
            "Roads",
            "Water Supply",
            "Electricity",
            "Garbage",
            "Drainage",
            "Other"
        ]

        if (
            not title
            or category not in allowed_categories
            or not location
            or not description
        ):
            flash("Please fill in all fields correctly.", "error")
            return redirect(url_for("new_complaint"))

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO complaints
            (user_id, title, category, location, description)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            title,
            category,
            location,
            description
        ))

        conn.commit()
        conn.close()

        flash("Your complaint was submitted successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("new_complaint.html")


# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin")
def admin():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        flash("You are not authorized to access this page.", "error")
        return redirect(url_for("dashboard"))

    conn = get_db_connection()

    complaints = conn.execute("""
        SELECT complaints.*, users.name, users.email
        FROM complaints
        JOIN users ON complaints.user_id = users.id
        ORDER BY complaints.id DESC
    """).fetchall()

    total = conn.execute(
        "SELECT COUNT(*) FROM complaints"
    ).fetchone()[0]

    pending = conn.execute(
        "SELECT COUNT(*) FROM complaints WHERE status = 'Pending'"
    ).fetchone()[0]

    resolved = conn.execute(
        "SELECT COUNT(*) FROM complaints WHERE status = 'Resolved'"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "admin.html",
        complaints=complaints,
        total=total,
        pending=pending,
        resolved=resolved
    )


# ---------------- UPDATE COMPLAINT STATUS ----------------

@app.route("/update-status/<int:complaint_id>", methods=["POST"])
def update_status(complaint_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        flash("You are not authorized to perform this action.", "error")
        return redirect(url_for("dashboard"))

    status = request.form.get("status")

    allowed_statuses = [
        "Pending",
        "In Progress",
        "Resolved"
    ]

    if status not in allowed_statuses:
        flash("Invalid complaint status.", "error")
        return redirect(url_for("admin"))

    conn = get_db_connection()

    conn.execute("""
        UPDATE complaints
        SET status = ?
        WHERE id = ?
    """, (status, complaint_id))

    conn.commit()
    conn.close()

    flash("Complaint status updated successfully.", "success")
    return redirect(url_for("admin"))


# ---------------- START APPLICATION ----------------

if __name__ == "__main__":
    init_db()
    app.run(debug=True)