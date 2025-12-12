# test_notification_api.py
import requests
import json

# Config
BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "your_jwt_token_here"  # Dapatkan dari login

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def test_notification_endpoints():
    print("=== TESTING NOTIFICATION API ENDPOINTS ===")
    
    # 1. Get notifications
    print("\n1. GET /notifications/")
    response = requests.get(
        f"{BASE_URL}/notifications/",
        headers=headers,
        params={"limit": 10}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total notifications: {len(data['notifications'])}")
        print(f"Total unread: {data['total_unread']}")
    
    # 2. Mark specific notification as read
    if response.status_code == 200 and data['notifications']:
        print("\n2. POST /notifications/{id}/read")
        notification_id = data['notifications'][0]['id']
        
        response = requests.post(
            f"{BASE_URL}/notifications/{notification_id}/read",
            headers=headers
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    
    # 3. Mark all as read
    print("\n3. POST /notifications/read-all")
    response = requests.post(
        f"{BASE_URL}/notifications/read-all",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    print("\n✅ API tests completed!")

if __name__ == "__main__":
    test_notification_endpoints()