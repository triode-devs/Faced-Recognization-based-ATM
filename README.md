# Face Biometric Authentication ATM System

A premium, secure ATM simulator built with **Flask**, **SQLite**, and **Deep Learning (DCNN/ResNet-34)** for face identification.

## 🚀 How to Run (From Clone)

Follow these steps to get the project running on your local machine:

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/Face-Biometric-ATM.git
cd Face-Biometric-ATM
```

### 2. Set Up Virtual Environment (Highly Recommended)
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```
> [!IMPORTANT]
> `dlib` (used for face recognition) requires **C++ Build Tools** installed on Windows. If the installation fails, search for "Visual Studio Build Tools with C++ desktop development" or use a pre-compiled wheel.

### 4. Patch for Python 3.12+ (If needed)
If you get a `ModuleNotFoundError: No module named 'pkg_resources'`, run:
```powershell
pip install setuptools
```
*(The `face_recognition_models` package may need a manual fix if using Python 3.12, see `app.py` for troubleshooting.)*

### 5. Launch the System
```powershell
python app.py
```

---

## 🔒 Usage Workflow

### 1. Register as Admin
1. Go to `http://localhost:5000/admin`.
2. Login: **`admin`** / **`admin123`**.
3. Create a new account (16-digit card number).
4. **Enroll Biometric**: Position your face and click "Enroll".

### 2. Use as Customer
1. Go to `http://localhost:5000`.
2. Enter your 16-digit card number.
3. **Face ID**: Let the scanner verify your identity.
4. **Dashboard**: Withdraw or Deposit funds securely.

---

## 🛠️ Tech Stack
- **Backend:** Flask / SQLite3
- **Biometrics:** `face_recognition` (dlib-based)
- **UI:** Tailwind CSS & Iconify (Standalone/Local)
- **Design:** Ultra-rounded premium POS aesthetic
