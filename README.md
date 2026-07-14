# trekking-management-app-v1
A trekking management web app built with Flask and Jinja2.
Three roles: Admin, Trek Staff, and Trekker.
---
## Prerequisites
- Python 3.x → https://www.python.org/downloads/
---
## How To Run

### Step 1 — Install Dependencies
pip install flask flask-sqlalchemy flask-login werkzeug

### Step 2 — Start The App
python app.py

Open browser at: http://localhost:5000
Admin is created automatically on first run.
---

## Login Credentials

| Role  | Username | Password |
|-------|----------|----------|
| Admin |  admin   | admin123 |

New trekkers can register at /register
Staff can self-register and await admin approval

---
## Notes
- No external services required
- Admin account pre-seeded on first run
