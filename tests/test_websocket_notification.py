# test_websocket_notification.py
import asyncio
import websockets
import json

async def test_websocket_notifications():
    """Test WebSocket untuk real-time notifications"""
    print("=== TESTING WEBSOCKET NOTIFICATIONS ===")
    
    # Ganti dengan token yang valid
    token = "your_jwt_token_here"
    ws_url = f"ws://localhost:8000/api/v1/ws/chat?token={token}"
    
    try:
        print(f"\nConnecting to {ws_url}...")
        async with websockets.connect(ws_url) as websocket:
            print("✅ Connected to WebSocket")
            
            # Subscribe to a thread
            subscribe_msg = {
                "type": "subscribe",
                "thread_id": "test_thread_123"
            }
            await websocket.send(json.dumps(subscribe_msg))
            print("✅ Sent subscribe message")
            
            # Listen for notifications
            print("\nListening for notifications (timeout: 10s)...")
            try:
                async for message in websocket:
                    data = json.loads(message)
                    print(f"\n📨 Received WebSocket message:")
                    print(f"   Type: {data.get('type')}")
                    
                    if data.get('type') == 'notification:new':
                        print("🎯 NOTIFICATION RECEIVED!")
                        print(f"   Title: {data['notification']['title']}")
                        print(f"   Message: {data['notification']['message']}")
                        break
                        
            except asyncio.TimeoutError:
                print("⏰ Timeout waiting for notification")
                
    except Exception as e:
        print(f"❌ WebSocket error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket_notifications())