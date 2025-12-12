# test_notification_service.py
import asyncio
import json
from datetime import datetime
from app.services.notification_service import notification_service

async def test_notification_flow():
    print("=== TESTING NOTIFICATION SERVICE ===")
    
    # 1. Test: Add notification to queue
    print("\n1. Testing notification queue...")
    notification_data = {
        "user_id": "user123",
        "title": "Pesan Baru",
        "message": "Anda menerima pesan baru dari John Doe",
        "notification_type": "message",
        "data": {
            "thread_id": "thread_abc123",
            "sender_id": "user456",
            "sender_name": "John Doe"
        },
        "thread_id": "thread_abc123"
    }
    
    await notification_service.add_to_queue(notification_data)
    print("✅ Notification added to queue")
    
    # Tunggu processing
    await asyncio.sleep(2)
    
    # 2. Test: Get user notifications
    print("\n2. Testing get user notifications...")
    result = await notification_service.get_user_notifications("user123", limit=10)
    notifications = result["notifications"]
    total_unread = result["total_unread"]
    
    print(f"📨 Notifications found: {len(notifications)}")
    print(f"🔴 Unread count: {total_unread}")
    
    if notifications:
        for notif in notifications[:3]:  # Show first 3
            print(f"  - ID: {notif['id']}")
            print(f"    Title: {notif['title']}")
            print(f"    Read: {notif['is_read']}")
    
    # 3. Test: Mark as read
    if notifications:
        print("\n3. Testing mark as read...")
        notification_id = notifications[0]['id']
        success = await notification_service.mark_as_read(notification_id, "user123")
        print(f"✅ Mark as read: {success}")
    
    # 4. Test: Mark all as read
    print("\n4. Testing mark all as read...")
    success = await notification_service.mark_all_as_read("user123")
    print(f"✅ Mark all as read: {success}")
    
    # 5. Test: Add device token
    print("\n5. Testing device registration...")
    # Ini perlu implementasi method add_device_token dulu
    # await notification_service.register_device("user123", "device_token_abc", "android")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_notification_flow())