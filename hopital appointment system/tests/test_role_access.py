import pytest
from flask import session

def test_unauthenticated_protected_route(client):
    """Verify unauthenticated user cannot access protected patient routes."""
    res = client.get("/patient/dashboard", follow_redirects=False)
    assert res.status_code == 302
    assert "/auth/login" in res.headers["Location"]

def test_patient_cannot_access_admin_dashboard(client, init_roles):
    """Verify patient role cannot access admin portal."""
    with client.session_transaction() as sess:
        sess["user_id"] = str(init_roles["patient_id"])
        sess["user_role"] = "patient"
        sess["user_name"] = "Test Patient"

    res = client.get("/admin/dashboard", follow_redirects=False)
    assert res.status_code in (302, 403)

def test_patient_cannot_access_doctor_dashboard(client, init_roles):
    """Verify patient cannot access doctor portal."""
    with client.session_transaction() as sess:
        sess["user_id"] = str(init_roles["patient_id"])
        sess["user_role"] = "patient"
        sess["user_name"] = "Test Patient"

    res = client.get("/doctor/dashboard", follow_redirects=False)
    assert res.status_code in (302, 403)

def test_doctor_cannot_access_admin_portal(client, init_roles):
    """Verify doctor role is restricted from admin management routes."""
    with client.session_transaction() as sess:
        sess["user_id"] = str(init_roles["doctor_id"])
        sess["user_role"] = "doctor"
        sess["user_name"] = "Test Doctor"

    res = client.get("/admin/doctors", follow_redirects=False)
    assert res.status_code in (302, 403)

def test_admin_can_access_admin_dashboard(client, init_roles):
    """Verify administrator has full authorized access to admin dashboard."""
    with client.session_transaction() as sess:
        sess["user_id"] = str(init_roles["admin_id"])
        sess["user_role"] = "admin"
        sess["user_name"] = "Admin User"

    res = client.get("/admin/dashboard")
    assert res.status_code == 200
    assert b"Administrative Dashboard" in res.data
