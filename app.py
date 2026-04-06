"""
╔══════════════════════════════════════════════════════════════════╗
║    FACE BIOMETRIC AUTHENTICATION SYSTEM FOR ATM                  ║
║    Deep Learning · Flask · Tailwind CSS · SQLite                 ║
║    Based on: S.SUMITHRA (814624483004) - Trichy Engineering      ║
╚══════════════════════════════════════════════════════════════════╝
Modules (from report):
  1. ATM Simulator        — Card entry + web UI
  2. Face Recognition     — Enrollment (Admin) + Authentication (User)
  3. Prediction           — DCNN comparison with Euclidean distance
  4. Unknown Face Forward — Alert link to card holder on mismatch
"""

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, flash
)
import os, base64, numpy as np, pickle, sqlite3, cv2
import face_recognition
from datetime import datetime
from functools import wraps
from database import (
    init_db, get_account, get_all_accounts,
    create_account, update_face_encoding,
    update_balance, log_transaction,
    update_failed_attempts, reset_failed_attempts,
    add_unknown_face, get_unknown_faces,
    resolve_unknown_face, get_transactions,
    get_admin, create_admin
)
from face_engine import encode_face_from_bytes, compare_faces

# ─── App Setup ──────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "atm_biometric_secret_2025"
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "faces")
UNKNOWN_FOLDER = os.path.join(os.path.dirname(__file__), "static", "unknown")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(UNKNOWN_FOLDER, exist_ok=True)


# ─── Auth Decorators ────────────────────────────────────
def atm_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "atm_card" not in session:
            return redirect(url_for("atm_card"))
        return f(*args, **kwargs)
    return decorated


def admin_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "admin_id" not in session:
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


# ══════════════════════════════════════════════════════════
#  ATM USER ROUTES
# ══════════════════════════════════════════════════════════

@app.route("/")
def index():
    return redirect(url_for("atm_card"))


@app.route("/atm")
def atm_card():
    """SCREEN 1 — Insert ATM Card"""
    session.clear()
    return render_template("atm_card.html")


@app.route("/verify-card", methods=["POST"])
def verify_card():
    """Verify 16-digit card number against database"""
    card = request.form.get("card_number", "").strip()
    account = get_account(card)

    if not account:
        flash("Card not found in our system.", "error")
        return redirect(url_for("atm_card"))

    if account["is_locked"]:
        flash("Your card has been locked due to too many failed attempts. Contact your bank.", "error")
        return redirect(url_for("atm_card"))

    session["atm_card"] = card
    session["holder_name"] = account["holder_name"]
    return redirect(url_for("face_scan"))


@app.route("/face-scan")
@atm_login_required
def face_scan():
    """SCREEN 2 — Face Biometric Scan"""
    card = session["atm_card"]
    account = get_account(card)
    has_face = account["face_encoding"] is not None
    return render_template("face_scan.html", account=account, has_face=has_face)


@app.route("/api/verify-face", methods=["POST"])
@atm_login_required
def api_verify_face():
    """
    API: Receive base64 webcam frame → run DCNN face comparison.
    Module 3: Prediction — Euclidean distance via ResNet-128d embeddings.
    """
    card = session["atm_card"]
    account = get_account(card)

    if not account["face_encoding"]:
        return jsonify({"status": "error", "message": "No face registered for this card."})

    data = request.get_json()
    img_b64 = data.get("image", "").split(",")[-1]

    try:
        img_bytes = base64.b64decode(img_b64)
        matched, confidence, live_encoding = compare_faces(
            account["face_encoding"], img_bytes
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

    failed = account["failed_attempts"]

    if matched:
        reset_failed_attempts(card)
        log_transaction(card, "LOGIN", 0)
        session["verified"] = True
        return jsonify({
            "status": "success",
            "confidence": confidence,
            "message": f"Identity Verified! Confidence: {confidence:.1f}%"
        })
    else:
        # Module 4: Unknown Face Forwarder
        new_failed = failed + 1
        lock = new_failed >= 3
        update_failed_attempts(card, new_failed, lock)

        # Save unknown face image
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"unknown_{card.replace(' ','')}_{ts}.jpg"
        fpath = os.path.join(UNKNOWN_FOLDER, fname)
        img_arr = np.frombuffer(img_bytes, np.uint8)
        img_cv  = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
        if img_cv is not None:
            cv2.imwrite(fpath, img_cv)
        add_unknown_face(card, fname)

        if lock:
            return jsonify({
                "status": "locked",
                "message": "Card locked! Too many failed attempts. Security team notified."
            })

        return jsonify({
            "status": "failed",
            "attempts_left": 3 - new_failed,
            "message": f"Face not recognized. {3 - new_failed} attempt(s) remaining.",
            "forward_link": url_for("unknown_forward", card=card, _external=True)
        })


@app.route("/dashboard")
@atm_login_required
def dashboard():
    """SCREEN 3 — Transaction Dashboard"""
    if not session.get("verified"):
        return redirect(url_for("face_scan"))
    card    = session["atm_card"]
    account = get_account(card)
    txns    = get_transactions(card, limit=5)
    return render_template("dashboard.html", account=account, txns=txns)


@app.route("/transaction/<tx_type>", methods=["GET", "POST"])
@atm_login_required
def transaction(tx_type):
    """Withdraw or Deposit"""
    if not session.get("verified"):
        return redirect(url_for("face_scan"))

    card    = session["atm_card"]
    account = get_account(card)

    if request.method == "POST":
        try:
            amount = float(request.form.get("amount", 0))
        except ValueError:
            flash("Invalid amount.", "error")
            return redirect(url_for("transaction", tx_type=tx_type))

        balance = account["balance"]

        if tx_type == "withdraw":
            if amount <= 0 or amount > balance:
                flash(f"Insufficient balance. Available: ₹{balance:,.2f}", "error")
                return redirect(url_for("transaction", tx_type=tx_type))
            update_balance(card, balance - amount)
            log_transaction(card, "WITHDRAW", amount)
            flash(f"₹{amount:,.2f} withdrawn successfully!", "success")

        elif tx_type == "deposit":
            if amount <= 0 or amount > 200000:
                flash("Invalid deposit amount. Max ₹2,00,000 per transaction.", "error")
                return redirect(url_for("transaction", tx_type=tx_type))
            update_balance(card, balance + amount)
            log_transaction(card, "DEPOSIT", amount)
            flash(f"₹{amount:,.2f} deposited successfully!", "success")

        return redirect(url_for("dashboard"))

    return render_template("transaction.html", account=account, tx_type=tx_type)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("atm_card"))


# ── Unknown Face Forwarder ──────────────────────────────
@app.route("/unknown-forward/<card>")
def unknown_forward(card):
    """Module 4 — Unknown Face Forwarder verification link sent to card holder"""
    account = get_account(card)
    if not account:
        return "Invalid request", 404
    unknowns = get_unknown_faces(card, pending_only=True)
    return render_template("unknown_forward.html", account=account, unknowns=unknowns)


@app.route("/unknown-forward/action", methods=["POST"])
def unknown_forward_action():
    """Card holder accepts or rejects the unknown face transaction"""
    face_id = request.form.get("face_id")
    action  = request.form.get("action")  # "accept" or "reject"
    card    = request.form.get("card")
    resolve_unknown_face(face_id, action)

    if action == "reject":
        update_failed_attempts(card, 3, True)  # lock card
        flash("Transaction rejected. Card blocked for security.", "error")
    else:
        flash("Transaction approved by card holder.", "success")

    return redirect(url_for("unknown_forward", card=card))


# ══════════════════════════════════════════════════════════
#  BANK ADMIN ROUTES
# ══════════════════════════════════════════════════════════

@app.route("/admin")
def admin_login():
    if "admin_id" in session:
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_login.html")


@app.route("/admin/auth", methods=["POST"])
def admin_auth():
    username = request.form.get("username")
    password = request.form.get("password")
    admin = get_admin(username, password)
    if admin:
        session["admin_id"]   = admin["id"]
        session["admin_name"] = admin["username"]
        return redirect(url_for("admin_dashboard"))
    flash("Invalid credentials.", "error")
    return redirect(url_for("admin_login"))


@app.route("/admin/dashboard")
@admin_login_required
def admin_dashboard():
    accounts = get_all_accounts()
    unknowns = get_unknown_faces(pending_only=True)
    return render_template("admin_dashboard.html",
                           accounts=accounts, unknowns=unknowns)


@app.route("/admin/add-account", methods=["GET", "POST"])
@admin_login_required
def admin_add_account():
    if request.method == "POST":
        card   = request.form.get("card_number", "").strip()
        name   = request.form.get("holder_name", "").strip()
        phone  = request.form.get("phone", "").strip()
        email  = request.form.get("email", "").strip()
        balance = float(request.form.get("balance", 5000))

        if not card or not name:
            flash("Card number and holder name are required.", "error")
            return redirect(url_for("admin_add_account"))

        try:
            create_account(card, name, phone, email, balance)
            flash(f"Account created for {name}. Now register their face.", "success")
            return redirect(url_for("admin_register_face", card=card))
        except Exception as e:
            flash(f"Error: {e}", "error")

    return render_template("admin_add_account.html")


@app.route("/admin/register-face/<card>")
@admin_login_required
def admin_register_face(card):
    """Face Enrollment — Admin registers beneficiary face"""
    account = get_account(card)
    if not account:
        flash("Account not found.", "error")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_register_face.html", account=account)


@app.route("/api/enroll-face", methods=["POST"])
@admin_login_required
def api_enroll_face():
    """
    API: Receive webcam frame → extract 128-d ResNet embedding → save to DB.
    Module 2: Face Enrollment — Preprocessing → Feature Extraction → Classification-CNN
    """
    data = request.get_json()
    card = data.get("card")
    img_b64 = data.get("image", "").split(",")[-1]

    try:
        img_bytes = base64.b64decode(img_b64)
        encoding  = encode_face_from_bytes(img_bytes)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

    if encoding is None:
        return jsonify({"status": "error", "message": "No face detected in frame. Please try again."})

    # Save face image
    fname = f"{card.replace(' ', '')}.jpg"
    fpath = os.path.join(UPLOAD_FOLDER, fname)
    img_arr = np.frombuffer(img_bytes, np.uint8)
    img_cv  = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
    if img_cv is not None:
        cv2.imwrite(fpath, img_cv)

    update_face_encoding(card, fname, pickle.dumps(encoding))
    return jsonify({"status": "success", "message": "Face enrolled successfully!"})


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_id", None)
    session.pop("admin_name", None)
    return redirect(url_for("admin_login"))


# ── Init & Run ──────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    create_admin("admin", "admin123")   # default admin
    print("\n" + "="*60)
    print("  ATM Biometric System running at http://127.0.0.1:5000")
    print("  Admin panel:  http://127.0.0.1:5000/admin")
    print("  Default login: admin / admin123")
    print("="*60 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
