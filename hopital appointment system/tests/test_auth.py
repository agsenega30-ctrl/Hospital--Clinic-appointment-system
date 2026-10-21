import pytest
from flask import session
from db import db

def test_patient_registration(client, app):
    """Test patient registration with validation."""
    with client:
        # Establish session to get CSRF token
        client.get("/auth/register")
        csrf_token = session.get("_csrf_token")

        res = client.post("/auth/register", data={
            "csrf_token": csrf_token,
            "full_name": "Alice Wonderland",
            "email": "alice@example.com",
            "password": "Password123",
            "confirm_password": "Password123",
            "phone": "+91 91234 56789",
            "role": "patient"
        }, follow_redirects=True)

        assert res.status_code == 200
        assert session.get("user_id") is not None
        assert session.get("user_role") == "patient"

        # Verify user exists in database with hashed password
        user = db.users.find_one({"email": "alice@example.com"})
        assert user is not None
        assert user["role"] == "patient"
        assert user["password_hash"] != "Password123"

def test_public_registration_cannot_create_admin(client, app):
    """Verify public registration cannot escalate privileges to admin."""
    with client:
        client.get("/auth/register")
        csrf_token = session.get("_csrf_token")

        client.post("/auth/register", data={
            "csrf_token": csrf_token,
            "full_name": "Hacker Attempt",
            "email": "hacker@example.com",
            "password": "Password123",
            "confirm_password": "Password123",
            "phone": "+91 99999 88888",
            "role": "admin"  # Malicious attempt
        }, follow_redirects=True)

        user = db.users.find_one({"email": "hacker@example.com"})
        assert user is not None
        assert user["role"] == "patient", "Role must be forced to patient"

def test_login_success(client, init_roles):
    """Test valid credential authentication."""
    with client:
        client.get("/auth/login")
        csrf_token = session.get("_csrf_token")

        res = client.post("/auth/login", data={
            "csrf_token": csrf_token,
            "email": "patient@test.com",
            "password": "Patient@123"
        }, follow_redirects=True)

        assert res.status_code == 200
        assert session.get("user_id") == str(init_roles["patient_id"])
        assert session.get("user_role") == "patient"

def test_login_invalid_password(client, init_roles):
    """Test invalid password rejection."""
    with client:
        client.get("/auth/login")
        csrf_token = session.get("_csrf_token")

        res = client.post("/auth/login", data={
            "csrf_token": csrf_token,
            "email": "patient@test.com",
            "password": "WrongPassword!"
        }, follow_redirects=True)

        assert res.status_code == 200
        assert session.get("user_id") is None
        assert b"Invalid email or password" in res.data

def test_login_nonexistent_user(client, app):
    """Test login attempt with unrecorded email."""
    with client:
        client.get("/auth/login")
        csrf_token = session.get("_csrf_token")

        res = client.post("/auth/login", data={
            "csrf_token": csrf_token,
            "email": "ghost@hospital.com",
            "password": "AnyPassword"
        }, follow_redirects=True)

        assert res.status_code == 200
        assert session.get("user_id") is None
        assert b"Invalid email or password" in res.data
