import requests

# Step 1: Create a session
session = requests.Session()

# Step 2: Define the login URL and payload
login_url = "https://getsafebox.app/safebox/login"
login_payload = {"access_key": "123 curve artist"}

# Step 3: Send POST request to log in
login_response = session.post(login_url, data=login_payload)

# Optional: Check if login succeeded
print("Login status code:", login_response.status_code)
print("Login response body:", login_response.text)

# Step 4: Make a request to a protected endpoint (cookies are preserved)
protected_url = "https://getsafebox.app/safebox/access"
response = session.get(protected_url)

# Step 5: Print the result
print("Protected content:")
print(response.text)

# Inspect cookies
print("\nCookies stored in session:")
for cookie in session.cookies:
    print(f"{cookie.name} = {cookie.value}")
