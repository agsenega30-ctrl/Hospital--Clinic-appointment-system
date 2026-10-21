# 🏥 Hospital & Clinic Appointment System

A modern, full-stack web application designed to simplify hospital and clinic appointment management. The system connects patients, doctors, and administrators through dedicated role-based dashboards, interactive calendar scheduling, doctor availability management, and appointment tracking.

Built using **Python, Flask, MongoDB, HTML5, CSS3, and JavaScript**, this project aims to make healthcare appointment scheduling more organized, accessible, and efficient.

## 📌 Table of Contents

- [Project Overview](#-project-overview)
- [Objectives](#-project-objectives)
- [Key Features](#-key-features)
- [User Roles](#-user-roles)
- [Technology Stack](#-technology-stack)
- [System Architecture](#-system-architecture)
- [Database Design](#-database-design)
- [Project Structure](#-project-structure)
- [Installation and Setup](#-installation-and-setup)
- [Environment Configuration](#-environment-configuration)
- [Running the Application](#-running-the-application)
- [Testing](#-testing)
- [Security Features](#-security-features)
- [Future Enhancements](#-future-enhancements)
- [Contributing](#-contributing)
- [License](#-license)

## 📖 Project Overview

The Hospital & Clinic Appointment System is a web-based healthcare management application that allows patients to discover doctors, check their availability, book appointments, and manage their consultations online.

Doctors can manage their working schedules, review appointments, and update consultation statuses. Administrators can oversee users, manage doctor accounts, monitor appointments, and view system analytics.

The application uses MongoDB to store application data and Python Flask to handle server-side logic, authentication, scheduling, and database operations. The frontend provides responsive interfaces for different user roles.

The project focuses on reducing manual appointment management, improving scheduling efficiency, and providing a centralized platform for hospital and clinic operations.

## 🎯 Project Objectives

- Digitize the hospital and clinic appointment booking process.
- Provide separate dashboards for patients, doctors, and administrators.
- Enable calendar-based appointment scheduling.
- Allow doctors to manage working hours, breaks, and unavailable dates.
- Prevent duplicate bookings and scheduling conflicts.
- Maintain appointment records in a database.
- Improve appointment visibility and communication through in-app notifications.
- Provide administrators with centralized management and analytics tools.
- Implement secure authentication and role-based access control.

## ✨ Key Features

### 1. Patient Dashboard

- Secure patient registration and login.
- Browse and search for doctors.
- Filter doctors by specialization and availability.
- View doctor profiles, qualifications, experience, and consultation fees.
- Check available dates and time slots.
- Book new appointments.
- View upcoming and previous appointments.
- Reschedule or cancel appointments according to system rules.
- View appointment details and booking status.
- Access an interactive appointment calendar.
- Receive in-app notifications about appointment updates.
- Update personal profile information and change passwords.

### 2. Doctor Dashboard

- View daily and upcoming appointment schedules.
- Monitor pending, confirmed, completed, and cancelled appointments.
- View relevant patient and consultation information.
- Confirm or reject appointment requests.
- Mark consultations as completed.
- Manage working days and consultation hours.
- Configure appointment duration and break times.
- Block unavailable dates for holidays, leave, or emergencies.
- Update doctor profiles, qualifications, specialization, and consultation fees.
- View appointments through daily, weekly, and monthly calendar views.

### 3. Admin Dashboard

- View overall system statistics.
- Monitor registered patients and doctors.
- Track appointment volumes and booking statuses.
- Create and manage doctor accounts.
- Approve or deactivate doctor accounts.
- View and manage patient accounts.
- Search and filter appointments.
- Manage medical specializations and departments.
- Configure clinic information and scheduling policies.
- View appointment analytics and graphical reports.
- Review administrative audit logs.

### 4. Appointment Booking and Scheduling

- Interactive calendar-based booking.
- Dynamic availability calculation based on doctor schedules.
- Automatic generation of available time slots.
- Validation of appointment dates and time slots.
- Prevention of double booking using database constraints.
- Appointment confirmation, cancellation, and rescheduling workflows.
- Appointment status tracking.
- Automatic updates to availability after booking changes.

### 5. Notifications

The system includes in-app notifications for important appointment events, including booking confirmations, rescheduling, and cancellations. Users can view their notifications and track which notifications have been read.

### 6. Responsive User Interface

- Modern healthcare-inspired design.
- Responsive layouts for desktop, tablet, and mobile devices.
- Role-specific navigation and dashboards.
- Interactive calendars, tables, forms, and status indicators.
- Dashboard charts and analytics.
- Form validation and user-friendly error messages.

## 👥 User Roles

| Role | Main Responsibilities |
|---|---|
| Patient | Discover doctors, book appointments, manage bookings, and update profiles. |
| Doctor | Manage availability, view appointments, and update consultation statuses. |
| Administrator | Manage users, doctors, appointments, specializations, and system settings. |

Each role has its own permissions. Patients cannot access administrative functions, and doctors are restricted to appointments and information they are authorized to view.

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Frontend | HTML5, CSS3, JavaScript |
| Backend | Python |
| Web Framework | Flask |
| Database | MongoDB |
| Database Integration | PyMongo |
| Authentication | Flask Sessions and Werkzeug password hashing |
| Calendar | FullCalendar |
| Data Visualization | Chart.js |
| Rate Limiting | Flask-Limiter |
| Testing | Pytest and Mongomock |
| Development Environment | Antigravity / Visual Studio Code |
| Version Control | Git and GitHub |

## 🏗️ System Architecture

The application follows a layered architecture:

1. **Presentation Layer:** HTML, CSS, and JavaScript provide the user interface.
2. **Application Layer:** Python Flask handles routes, authentication, authorization, and business logic.
3. **Service Layer:** Appointment and doctor services manage scheduling rules, availability, notifications, and related operations.
4. **Database Layer:** MongoDB stores users, doctors, appointments, notifications, and other application records.
5. **Testing Layer:** Automated tests validate authentication, role permissions, database behavior, and scheduling logic.

## 🗄️ Database Design

The system uses MongoDB as its primary database.

The main data groups include:

- **Users:** Account details, roles, credentials, and account status.
- **Doctors:** Medical profiles, qualifications, specialization, consultation fees, and availability.
- **Appointments:** Patient and doctor references, date, time, booking reason, and appointment status.
- **Specializations:** Medical departments and their configuration.
- **Notifications:** User notifications and read status.
- **Audit Logs:** Records of relevant administrative and security-related actions.
- **Settings:** Clinic information and configurable scheduling policies.

MongoDB indexes and database-level constraints help improve query performance and protect appointment booking integrity.

## 📂 Project Structure

```text
hospital_appointment_system/
├── app.py
├── config.py
├── db.py
├── extensions.py
├── seed.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── routes/
│   ├── auth.py
│   ├── public.py
│   ├── patient.py
│   ├── doctor.py
│   ├── admin.py
│   ├── appointments.py
│   └── notifications.py
│
├── services/
│   ├── appointment_service.py
│   ├── doctor_service.py
│   ├── notification_service.py
│   └── audit_service.py
│
├── templates/
│   ├── base.html
│   ├── base_dashboard.html
│   ├── index.html
│   ├── auth/
│   ├── patient/
│   ├── doctor/
│   ├── admin/
│   ├── public/
│   └── shared/
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── main.js
│       ├── appointments.js
│       └── calendar.js
│
└── tests/
    ├── conftest.py
    ├── test_auth.py
    ├── test_database.py
    ├── test_role_access.py
    └── test_scheduling.py
```

## ⚙️ Installation and Setup

### Prerequisites

Install the following software before running the project:

- Python 3.10 or later.
- MongoDB Community Server or a MongoDB Atlas account.
- Git.
- A code editor such as Visual Studio Code or Antigravity.

### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/hospital-clinic-appointment-system.git
cd hospital-clinic-appointment-system
```

Replace `YOUR-USERNAME` with your GitHub username.

### Step 2: Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a local `.env` file using `.env.example` as a template.

Configure your Flask secret key, MongoDB connection URI, database name, timezone, and initial administrator credentials.

### Step 5: Configure MongoDB

For a local MongoDB installation, use:

```env
MONGO_URI=mongodb://localhost:27017/hospital_appointment_system
MONGO_DB_NAME=hospital_appointment_system
APP_TIMEZONE=Asia/Kolkata
```

Alternatively, configure your MongoDB Atlas connection URI in the local `.env` file.

Ensure that the database server is running and the application has permission to connect.

### Step 6: Initialize Demo Data

If the project's seed script is configured for your environment, initialize the database using:

```bash
flask --app app seed-db
```

Review `seed.py` and your local environment configuration before running the command. Use only test accounts and change any initial administrator password before using the application beyond local development.

## 🚀 Running the Application

Start the Flask development server:

```bash
python app.py
```

Open your browser and navigate to:

**http://127.0.0.1:5000**

The application should display the landing page when the server and database are configured correctly.

For local development, use the Flask development server only. Configure a production WSGI server and appropriate security settings before deployment.

## 🧪 Testing

The project includes automated tests for important application workflows.

Run the test suite using:

```bash
pytest -v
```

Testing areas include:

- User registration and login.
- Authentication and role-based access control.
- Database connection behavior.
- Appointment availability and scheduling.
- Prevention of duplicate bookings.
- Appointment ownership and authorization rules.

Tests should be run in an isolated test environment without using real patient data or production credentials.

## 🔐 Security Features

- Password hashing instead of plain-text password storage.
- Session-based authentication.
- Role-based authorization.
- Server-side input validation.
- CSRF protection for applicable requests.
- Login rate limiting.
- Appointment ownership checks.
- Database constraints to help prevent duplicate bookings.
- Restricted administrative functions.
- Environment-based configuration for secrets.
- Audit logging for relevant administrative actions.

**Security note:** This project is intended for educational and development purposes. A real healthcare deployment requires additional security reviews, privacy controls, operational safeguards, and compliance with applicable healthcare and data protection requirements.

## 🔮 Future Enhancements

Possible future improvements include:

- Email and SMS appointment reminders.
- Online payment integration.
- Video consultation support.
- Prescription and medical record management.
- Automated waiting lists.
- Multi-clinic and multi-hospital support.
- Advanced reporting and exportable analytics.
- Progressive Web App support.
- Multilingual user interfaces.
- Cloud deployment and automated backups.

These are proposed enhancements and may not be implemented in the current version.

## 🤝 Contributing

Contributions and suggestions are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Implement and test your changes.
4. Commit your changes with a descriptive message.
5. Open a pull request describing the improvement.

Please avoid committing credentials, local environment files, virtual environments, or real patient information.

## 📄 License

No license has been specified yet. Add an appropriate open-source license file if you intend to allow others to use, modify, and distribute this project.

## 👨‍💻 Author

**Mohan Raj Balakrishnan**

Electronics and Communication Engineering (ECE)

GitHub: Add your GitHub profile URL here.

## ⭐ Acknowledgements

This project was developed as a software application project to explore web development, database integration, appointment scheduling, authentication, and role-based healthcare management.

If you find this project useful, consider giving the repository a star on GitHub.

---

**Project:** Hospital & Clinic Appointment System  
**Backend:** Python + Flask  
**Frontend:** HTML + CSS + JavaScript  
**Database:** MongoDB  
**Purpose:** Digital healthcare appointment and scheduling management.
