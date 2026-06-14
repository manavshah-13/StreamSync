import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/auth"

def test_auth():
    print("Testing Signup...")
    signup_data = {
        "email": "test_user_unique@example.com",
        "full_name": "Test User",
        "password": "password123"
    }
    try:
        r = requests.post(f"{BASE_URL}/signup", json=signup_data)
        print(f"Signup Status: {r.status_code}")
        print(f"Signup Response: {r.text}")
        
        if r.status_code == 200 or r.status_code == 400: # 400 if already exists
            print("\nTesting Login...")
            login_data = {"username": signup_data["email"], "password": signup_data["password"]}
            r_login = requests.post(f"{BASE_URL}/login", data=login_data)
            print(f"Login Status: {r_login.status_code}")
            print(f"Login Response: {r_login.text}")
            
            if r_login.status_code == 200:
                token = r_login.json()["access_token"]
                print("\nTesting Me...")
                r_me = requests.get(f"{BASE_URL}/me", headers={"Authorization": f"Bearer {token}"})
                print(f"Me Status: {r_me.status_code}")
                print(f"Me Response: {r_me.text}")
                
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_auth()
