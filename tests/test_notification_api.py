# test_notification_api.py
import httpx
import asyncio
import json

# Config
BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "your_jwt_token_here"  # Dapatkan dari login

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

async def test_notification_endpoints():
    print("=== TESTING NOTIFICATION API ENDPOINTS ===")
    
    async with httpx.AsyncClient() as client:
        # 1. Get notifications
        print("\n1. GET /notifications/")
        response = await client.get(
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
            
            response = await client.post(
                f"{BASE_URL}/notifications/{notification_id}/read",
                headers=headers
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        
        # 3. Mark all as read
        print("\n3. POST /notifications/read-all")
        response = await client.post(
            f"{BASE_URL}/notifications/read-all",
            headers=headers
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    
    print("\n✅ API tests completed!")

if __name__ == "__main__":
    asyncio.run(test_notification_endpoints())