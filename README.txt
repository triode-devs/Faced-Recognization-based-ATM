╔═══════════════════════════════════════════════════════════════════╗
║   FACE BIOMETRIC AUTHENTICATION SYSTEM FOR ATM — FLASK WEB APP   ║
║   S.SUMITHRA (814624483004) · Trichy Engineering College          ║
║   Guide: Mrs. P. NITHILA, B.E., M.E., (PhD) · Dept. of ECE       ║
╚═══════════════════════════════════════════════════════════════════╝

ARCHITECTURE (from report)
──────────────────────────
  Module 1: ATM Simulator        — Flask web app, card entry
  Module 2: Face Recognition     — Enrollment (Admin) + Authentication (User)
             Pipeline: Frame → Preprocessing → Segmentation →
                       Feature Extraction → Classification-CNN (ResNet)
  Module 3: Prediction           — Euclidean distance match
  Module 4: Unknown Face Forward — Alert link sent to card holder

TECH STACK
──────────
  Backend    : Python 3.10 + Flask 2.x
  Deep Learning: face_recognition (dlib ResNet-34, 128-d embeddings)
  Vision     : OpenCV (frame preprocessing, denoising)
  Database   : SQLite (equivalent to MySQL schema from report)
  Frontend   : Tailwind CSS (CDN) — dark ATM terminal aesthetic
  Templates  : Jinja2 HTML templates

PROJECT STRUCTURE
─────────────────
  app.py                     ← Flask routes (all 4 modules)
  face_engine.py             ← DCNN face recognition pipeline
  database.py                ← SQLite data layer
  requirements.txt
  atm_biometric.db           ← Auto-created on first run
  templates/
    base.html                ← Tailwind CSS base layout
    atm_card.html            ← Card entry screen
    face_scan.html           ← Webcam face verification
    dashboard.html           ← Transaction dashboard
    transaction.html         ← Withdraw / Deposit
    unknown_forward.html     ← Module 4: Unknown face alert
    admin_login.html         ← Admin login
    admin_dashboard.html     ← Admin overview
    admin_add_account.html   ← Create bank account
    admin_register_face.html ← Face enrollment (Admin)
  static/
    faces/                   ← Enrolled face images
    unknown/                 ← Unknown face captures

SETUP
─────
1. Install cmake (required for dlib)
   Windows: cmake.org → Add to PATH
   Linux:   sudo apt install cmake build-essential libopenblas-dev

2. Create virtual environment
   python -m venv venv
   venv\Scripts\activate         (Windows)
   source venv/bin/activate      (Linux/macOS)

3. Install dependencies
   pip install -r requirements.txt
   (dlib takes 5-10 min to compile — normal)

4. Run the server
   python app.py

5. Open browser: http://localhost:5000

WORKFLOW
────────
BANK ADMIN SETUP:
  → http://localhost:5000/admin
  → Login: admin / admin123
  → Add Account → Enter card, name, balance
  → Register Face (webcam opens, align face, click Capture & Enroll)
  → CNN extracts 128-d embedding → saved to DB

USER ATM SESSION:
  → http://localhost:5000
  → Enter 16-digit card number
  → Webcam opens → position face → click SCAN FACE
  → ResNet model extracts embedding → Euclidean distance
  → If distance ≤ 0.50 → VERIFIED → Transaction Dashboard
  → If mismatch → fail counter increments, face saved as unknown
  → 3 failures → card locked

MODULE 4 — UNKNOWN FACE FORWARDER:
  → On mismatch, unknown face image saved
  → Link: /unknown-forward/<card>
  → Card holder sees the captured image
  → Clicks YES (its me) or NO (block card)
  → In production: this link is emailed/SMS'd to registered phone/email

DEMO ACCOUNTS (pre-seeded)
───────────────────────────
  Card                  | Holder         | Balance
  ──────────────────────|────────────────|──────────
  1234 5678 9012 3456   | Sumithra S     | ₹10,000
  9876 5432 1098 7654   | Priya Nair     | ₹7,500
  1111 2222 3333 4444   | Arjun Menon    | ₹3,200
  (Register faces via admin panel first)

FACE MATCHING TOLERANCE
───────────────────────
  Edit face_engine.py:
  TOLERANCE = 0.50   # default (balanced)
  TOLERANCE = 0.40   # strict (fewer false positives)
  TOLERANCE = 0.60   # lenient

NOTES
─────
  • Tailwind CSS loaded from CDN — internet required
  • For offline use, download tailwind.min.css and update base.html
  • SQLite used for portability; replace with MySQL for production
    (schema is identical — change get_conn() in database.py)
  • Browser webcam requires HTTPS in production (use Flask-HTTPS or nginx)
