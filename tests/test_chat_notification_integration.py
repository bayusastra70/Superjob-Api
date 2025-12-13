# test_chat_notification_integration.py
import asyncio
from app.services.chat_service import ChatService
from app.schemas.chat import MessageCreate

async def test_chat_triggers_notification():
    """Test bahwa chat message memicu notification"""
    print("=== TESTING CHAT → NOTIFICATION FLOW ===")
    
    chat_service = ChatService()
    
    # Simulasikan pengiriman pesan
    message_data = MessageCreate(
        thread_id="test_thread_123",
        receiver_id="user456",  # Penerima
        message_text="Halo, ini pesan test!",
        is_ai_suggestion=0
    )
    
    print("\n1. Sending test message...")
    message_id = await chat_service.send_message(
        sender_id="user123",  # Pengirim
        sender_name="Test User",
        message_data=message_data
    )
    
    print(f"✅ Message sent: {message_id}")
    
    # Tunggu notification diproses
    await asyncio.sleep(1)
    
    # Cek notification di database
    from app.services.database import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) as count FROM notifications 
        WHERE user_id = %s AND thread_id = %s
    """, ("user456", "test_thread_123"))
    
    count = cursor.fetchone()['count']
    print(f"\n2. Notifications created for receiver: {count}")
    
    if count > 0:
        cursor.execute("""
            SELECT title, message, is_read FROM notifications 
            WHERE user_id = %s 
            ORDER BY created_at DESC LIMIT 1
        """, ("user456",))
        
        notif = cursor.fetchone()
        print(f"📨 Latest notification:")
        print(f"   Title: {notif['title']}")
        print(f"   Message: {notif['message']}")
        print(f"   Read: {notif['is_read']}")
    
    conn.close()
    print("\n✅ Integration test completed!")

if __name__ == "__main__":
    asyncio.run(test_chat_triggers_notification())