# Face Recognition ATM (TrustPay) — User Guide

This guide covers the full setup and operational workflow for the Face Biometric ATM project.

## 🛠️ Step 1: Initial Setup

1.  **Open Terminal** in the project folder: `d:\Projects\Faced Recognization based ATM`.
2.  **Verify Virtual Environment**: A virtual environment (`venv`) manages the specialized libraries (OpenCV, dlib).
    ```powershell
    .\venv\Scripts\activate
    ```
3.  **Install Requirements** (if not already done):
    ```powershell
    pip install -r requirements.txt
    ```
4.  **Launch the Server**:
    ```powershell
    python app.py
    ```
    Once running, open the following URLs in your browser:
    -   **Admin Portal**: `http://localhost:5000/admin`
    -   **ATM Simulator**: `http://localhost:5000/atm`

---

## 🔒 Step 2: Bank Admin Enrollment (Workflow)

Before a user can use the ATM, they must be registered in the system.

1.  **Login as Admin**: Access `http://localhost:5000/admin`.
    -   Username: `admin`
    -   Password: `admin123`
2.  **Add Account**: Click the **Create Account** button.
    -   Enter a **16-digit card number** (e.g., `1234 5678 9012 3456`).
    -   Enter the **Legal Name** and initial **Balance**.
3.  **Biometric Enrollment**: After adding the account, you will be prompted to **Enroll Face**.
    -   Position your face within the scanner frame.
    -   Ensuring good lighting, click **Enroll Biometric**.
    -   The system will extract a 128-dimensional embedding from your face and save it to the database securely.

---

## 🏧 Step 3: ATM Transaction Flow (User)

1.  **Insert Card**: Access `http://localhost:5000/atm`.
    -   Enter the registered **16-digit card number**.
2.  **Face Identity Verification**:
    -   Position your face in the camera.
    -   Click **Verify Identity**.
    -   If the match confidence is high enough, the door to the dashboard will open.
3.  **Manage Funds**:
    -   **Withdraw**: Enter amount to subtract from your balance.
    -   **Deposit**: Enter amount to add.
    -   View **Recent Activity** at the bottom of the dashboard.
4.  **End Session**: Click the red **End Session** button to logout.

---

## 🛡️ Security Alerts (Module 4)

If someone else tries to access your account:
1.  The system captures an **Unknown Face** image.
2.  A security link is generated: `/unknown-forward/<card>`.
3.  On this page, you can see the captured image and choose to:
    -   **Block Card**: Instantly locks the account due to unauthorized access.
    -   **It is Me**: Overwrites the security check once if you were the one at the terminal.

---

## ⚡ Troubleshooting

-   **Camera Error**: Ensure no other application (like Zoom/Discord) is currently using your webcam.
-   **No Face Detected**: Ensure your face is centered and well-lit.
-   **Lockout**: If a user fails verification 3 times, their card is automatically locked by the admin.
