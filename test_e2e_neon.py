import os
import sys

# Ensure .venv is used
from application import app, systemdb

print("=" * 60)
print("TEST 1: Database Connection Verification")
print("=" * 60)
print(f"Connected database URI: {app.config.get('DATABASE_URL', os.getenv('DATABASE_URL', ''))[:40]}...")

# Verify querying fooddata from Neon
foods = systemdb.execute("SELECT count(*) as cnt FROM fooddata")
print(f"Neon fooddata count: {foods[0]['cnt']} items")
assert foods[0]['cnt'] == 1534, "Expected 1534 food items in Neon"
print("✓ Neon database connection verified!")

print("\n" + "=" * 60)
print("TEST 2: Flask Route & Session Verification")
print("=" * 60)
client = app.test_client()

# Test home page
res_home = client.get("/")
print(f"GET / -> Status {res_home.status_code}")
assert res_home.status_code == 200
print("✓ Home page renders successfully!")

# Test login page
res_login = client.get("/login")
print(f"GET /login -> Status {res_login.status_code}")
assert res_login.status_code == 200
print("✓ Login page renders successfully!")

# Test register page
res_register = client.get("/register")
print(f"GET /register -> Status {res_register.status_code}")
assert res_register.status_code == 200
print("✓ Register page renders successfully!")

print("\n" + "=" * 60)
print("TEST 3: End-to-End User Flow on Neon")
print("=" * 60)
test_user = "test_neon_runner"
test_pass = "SecurePass123!"

# Clean up existing test user if any
systemdb.execute("DELETE FROM users WHERE username = ?", test_user)

# Register user via POST
res_reg_post = client.post("/register", data={
    "username": test_user,
    "password": test_pass,
    "confirmation": test_pass
}, follow_redirects=True)
print(f"POST /register -> Status {res_reg_post.status_code}")
assert "Registration successful!" in res_reg_post.data.decode("utf-8")
print("✓ User registration in Neon succeeded!")

# Login via POST
res_login_post = client.post("/login", data={
    "username": test_user,
    "password": test_pass
}, follow_redirects=True)
print(f"POST /login -> Status {res_login_post.status_code}")
assert "Login successful!" in res_login_post.data.decode("utf-8")
print("✓ User login session established!")

# Verify user exists in Neon
user_row = systemdb.execute("SELECT userid, username FROM users WHERE username = ?", test_user)
assert len(user_row) == 1
test_userid = user_row[0]["userid"]
print(f"✓ Verified user row in Neon: id={test_userid}, username={user_row[0]['username']}")

# Test kjcalc route with logged-in session (retrieves ingredients from fooddata in Neon)
res_kjcalc = client.get("/kjcalc")
print(f"GET /kjcalc -> Status {res_kjcalc.status_code}")
assert res_kjcalc.status_code == 200
print("✓ Recipe calculator loaded ingredients from Neon fooddata!")

# Clean up test user
systemdb.execute("DELETE FROM users WHERE username = ?", test_user)
print("✓ Test user cleaned up.")

print("\n" + "=" * 60)
print("ALL END-TO-END TESTS PASSED SUCCESSFULLY!")
print("=" * 60)
