# Hospital & Clinic Appointment System

A full-stack, responsive, and secure Hospital/Clinic Appointment System built with Python, Flask, PyMongo, HTML5, CSS3, vanilla JavaScript, FullCalendar, and Chart.js.

The system connects patients, doctors, and hospital administrators with role-based dashboards, atomic double-booking prevention, real-time availability calculation, interactive calendar scheduling, and in-app notifications.

---

## 🚀 Key Features

### 1. Patient Portal
- **Secure Authentication:** Registration with validation and Werkzeug password hashing.
- **Doctor Discovery:** Search doctors by name, filter by clinical specialization and availability date.
- **Doctor Profiles:** View qualifications, experience, consultation fees, working days, and hours.
- **Dynamic Scheduling:** Slot generation enforces doctor's working hours, break times, and blocked dates.
- **Concurrency-Safe Atomic Booking:** Unique database constraints prevent simultaneous double-booking.
- **Appointment Management:** Filter upcoming, past, completed, and cancelled visits.
- **Rescheduling & Cancellation:** Reschedule to new slots or cancel with recorded reasons.
- **Interactive Calendar:** Personal calendar with color-coded appointment statuses.
- **In-App Notifications:** Real-time alerts for booking confirmation, reschedule, and cancellation.

### 2. Doctor Portal
- **Daily Consultation Queue:** Dashboard tracking today's appointments, pending requests, and completions.
- **Interactive Calendar:** Daily, weekly, and monthly FullCalendar views with status color-coding.
- **Schedule Configuration:** Set active working days, working hours, break/lunch intervals, and slot duration.
- **Blocked Dates Management:** Block vacation, leave, or emergency out-of-clinic dates.
- **Consultation Management:** Confirm pending appointments, mark consultations as completed, or reject with reason.
- **Profile & Fee Settings:** Update qualifications, specialization, consultation fees, and biography.

### 3. Administrator Portal
- **Executive Analytics:** High-level metrics tracking total patients, doctors, appointments, cancellations, and pending registrations.
- **Visual Reports (Chart.js):**
  - Donut chart of appointment status breakdown (Pending, Confirmed, Completed, Cancelled).
  - Bar chart of consultations per medical department.
  - Line graph of monthly appointment volume trends.
- **Doctor Account Management:** Create doctor accounts, activate, deactivate, or approve self-registered doctors.
- **Patient Account Directory:** View registered patients, consultation history, and toggle account status.
- **Master Appointment Oversight:** Filter all clinic appointments by date, status, or doctor.
- **Department / Specialization Manager:** Add, edit, and toggle active medical departments.
- **Security Audit Logs:** Immutable audit trail recording timestamps, actors, actions, targets, and details.
- **Platform Configuration:** Hospital identity, contact information, cancellation notice lead times, and self-registration policies.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.10+ / 3.14+, Flask 3.x |
| **Database** | MongoDB 6.0+ via PyMongo |
| **Testing DB** | mongomock (in-memory mock database for automated test suite) |
| **Authentication** | Secure Flask Session with Werkzeug password hashing |
| **Rate Limiting** | Flask-Limiter |
| **Calendar** | FullCalendar v6 (DayGrid, TimeGrid views) |
| **Analytics & Charts** | Chart.js v4 |
| **Frontend** | HTML5, Responsive Vanilla CSS3, Vanilla JavaScript (ES6+) |
| **Icons & Typography**| Font Awesome 6, Google Fonts (Inter) |

---

## 📂 Project Directory Structure

```text
hospital_appointment_system/
├── app.py                      # Flask application factory & CLI commands
├── config.py                   # Configuration classes (Dev, Prod, Test)
├── db.py                       # PyMongo connection manager & index initialization
├── extensions.py               # Rate limiter, CSRF token middleware, auth decorators
├── seed.py                     # Demo data generator & initial admin setup
├── requirements.txt            # Python dependencies
├── .env.example                # Documented environment variables template
├── .env                        # Local development environment configuration
├── README.md                   # Installation, setup, and architecture documentation
│
├── routes/
│   ├── auth.py                 # Login, registration, logout, and lockout protection
│   ├── public.py               # Landing page, doctor directory, doctor detail, contact
│   ├── patient.py              # Patient dashboard, booking, appointments, calendar, profile
│   ├── doctor.py               # Doctor dashboard, calendar, queue, availability, profile
│   ├── admin.py                # Admin dashboard, doctors, patients, audit logs, settings
│   ├── appointments.py         # AJAX APIs for slot calculation, booking, rescheduling, events
│   └── notifications.py        # In-app notifications feed and read tracking
│
├── services/
│   ├── appointment_service.py  # Slot calculation, double-booking prevention, status lifecycle
│   ├── doctor_service.py       # Doctor profiles, search, filtering, and schedule management
│   ├── notification_service.py # In-app notification delivery and read counters
│   └── audit_service.py        # Immutable audit logging for actions and compliance
│
├── static/
│   ├── css/
│   │   └── style.css           # Clean healthcare design system, cards, tables, badges, modals
│   └── js/
│       ├── main.js             # CSRF fetch helper, notification dropdown, mobile drawer, toasts
│       ├── appointments.js     # Real-time slot loader, cancel modal, reschedule modal, status
│       └── calendar.js         # FullCalendar initialization, status colors, event modals
│
├── templates/
│   ├── base.html               # Main HTML5 skeleton, navbar, footer, modals, and CDN links
│   ├── base_dashboard.html     # Role-based dashboard shell with sidebar & topbar
│   ├── index.html              # Public landing page with hero, specialties, featured doctors
│   ├── shared/
│   │   ├── _alerts.html        # Flash alert messages
│   │   ├── error.html          # Standardized HTTP error view (400, 403, 429, 500)
│   │   ├── 404.html            # Not found page
│   │   └── notifications.html  # Full notifications list
│   ├── public/
│   │   ├── doctors.html        # Public searchable doctor directory
│   │   ├── doctor_detail.html  # Public doctor profile & booking CTA
│   │   └── contact.html        # Contact desk & inquiry form
│   ├── auth/
│   │   ├── login.html          # Secure login with demo credential quick-fill
│   │   └── register.html       # Patient / doctor registration
│   ├── patient/
│   │   ├── dashboard.html      # Patient KPI cards, upcoming consultations
│   │   ├── book_appointment.html# Doctor picker, date picker, slot loader, and submit
│   │   ├── my_appointments.html# Patient appointment list with status filters
│   │   ├── appointment_detail.html# Full consultation record
│   │   ├── calendar.html       # FullCalendar patient view
│   │   └── profile.html        # Profile update and password change
│   ├── doctor/
│   │   ├── dashboard.html      # Today's queue and consultation metrics
│   │   ├── calendar.html       # FullCalendar physician schedule view
│   │   ├── appointments.html   # Patient list with confirm/complete/cancel controls
│   │   ├── availability.html   # Working days, hours, breaks, and blocked dates
│   │   └── profile.html        # Medical credentials, fee, and biography
│   └── admin/
│       ├── dashboard.html      # Executive overview, approval alerts, Chart.js preview
│       ├── doctors.html        # Doctor management table & Add Doctor modal
│       ├── patients.html       # Patient directory and account status toggles
│       ├── appointments.html   # Master appointments directory and filters
│       ├── specializations.html# Clinical department management
│       ├── analytics.html      # Chart.js analytics reports
│       ├── audit_logs.html     # System activity & security audit trail
│       └── settings.html       # Clinic identity & scheduling rules
│
└── tests/
    ├── conftest.py             # Test fixtures & in-memory database configuration
    ├── test_auth.py            # Registration, login, and privilege escalation tests
    ├── test_role_access.py     # Role-based authorization & route protection tests
    ├── test_scheduling.py      # Slot calculation, double-booking, and ownership tests
    └── test_database.py        # Connection failure resilience & mongomock tests
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
- Python 3.10 or higher (Python 3.14 compatible)
- MongoDB Community Server or MongoDB Atlas account

### 2. Clone or Navigate to Project
```bash
cd "d:/project/hopital appointment system"
```

### 3. Setup Virtual Environment
```bash
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# On Linux / macOS:
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🗄️ MongoDB Configuration Instructions

### Option A: Local MongoDB Server
1. Download and install **MongoDB Community Server** from [mongodb.com](https://www.mongodb.com/try/download/community).
2. Start the MongoDB service:
   - On Windows: Run `net start MongoDB` in an administrator command prompt or start through `services.msc`.
   - On Linux: Run `sudo systemctl start mongod`.
3. Configure your `.env` file:
   ```env
   MONGO_URI=mongodb://localhost:27017/hospital_appointment_system
   MONGO_DB_NAME=hospital_appointment_system
   ```

### Option B: MongoDB Atlas (Cloud)
1. Create a free M0 cluster on [MongoDB Atlas](https://www.mongodb.com/atlas).
2. Under **Database Access**, create a database user (e.g., `hospital_admin`).
3. Under **Network Access**, whitelist your IP address (or `0.0.0.0/0` for development).
4. Click **Connect** -> **Drivers (Python)** and copy the connection string.
5. In your `.env` file:
   ```env
   MONGO_URI=mongodb+srv://<username>:<password>@cluster0.xxxx.mongodb.net/hospital_appointment_system?retryWrites=true&w=majority
   MONGO_DB_NAME=hospital_appointment_system
   ```

> **Note on Offline Resilience:** If MongoDB is currently stopped or unreachable, the application starts gracefully and informs the user via a top banner without crashing.

---

## 🧪 Database Seeding (Demo Records)

To initialize clinical specializations, demo doctors, sample patients, and default administrator credentials, execute:

```bash
.venv\Scripts\python seed.py
```

To clean existing collections before seeding:
```bash
.venv\Scripts\python seed.py --clean
```

### Default Demo Accounts

| Role | Email | Password | Access / Scope |
|---|---|---|---|
| **Admin** | `admin@hospital.com` | `Admin@Hospital2026` | Full administrative control |
| **Doctor** | `sarah.jenkins@hospital.com` | `Doctor@123456` | Cardiology specialist schedule |
| **Doctor** | `rajesh.sharma@hospital.com` | `Doctor@123456` | General Medicine schedule |
| **Patient** | `patient@hospital.com` | `Patient@123456` | Booking and personal history |

*(Tip: The login page includes quick-fill buttons for instant testing and presentation).*

---

## 🧪 Running Automated Tests

Run the test suite using `pytest`:

```bash
.venv\Scripts\python -m pytest -v
```

All 20 test cases execute against an isolated in-memory test database (`mongomock`), ensuring tests run quickly and never modify your development data.

### Test Coverage Highlights:
- **Authentication & Validation:** Patient registration, secure password hashing, invalid credentials, non-existent users.
- **Privilege Escalation Prevention:** Enforces that public registration can never create administrative accounts.
- **Role-Based Access Control:** Role decorators strictly restrict patients and doctors from unauthorized areas.
- **Atomic Double-Booking Prevention:** Ensures two users cannot book the same slot.
- **Doctor Schedule Constraints:** Rejects bookings outside working hours, during breaks, or on past dates.
- **Patient Data Ownership:** Ensures patients can only access and cancel their own appointments.
- **Rescheduling & Cancellation:** Validates status lifecycle and reason tracking.
- **Database Failure Resilience:** Validates graceful handling of unreachable MongoDB instances.

---

## 💻 Running the Application

Start the Flask development server:

```bash
.venv\Scripts\python app.py
```

The application will be live at:
```text
http://127.0.0.1:5000
```

---

## 🔒 Security Best Practices Implemented

1. **Password Hashing:** Passwords are never stored in plain-text; hashed using Werkzeug PBKDF2/SHA256.
2. **CSRF Protection:** State-changing requests (`POST`, `PUT`, `DELETE`) require a valid session CSRF token sent via header (`X-CSRFToken`) or form input.
3. **Session Cookie Security:** `HttpOnly=True` prevents JavaScript access; `SameSite=Lax` prevents CSRF cross-origin attacks.
4. **Rate Limiting:** Auth endpoints (`/auth/login`, `/auth/register`) are rate-limited via `Flask-Limiter` to protect against brute-force attacks.
5. **Role-Based Access Control (RBAC):** Every endpoint strictly checks the session user role before rendering or modifying data.
6. **NoSQL Injection Defense:** Inputs are strictly cast or verified before building MongoDB queries.
7. **Comprehensive Audit Logging:** System actions (registrations, logins, appointments, status updates, settings) are logged in the `audit_logs` collection.
