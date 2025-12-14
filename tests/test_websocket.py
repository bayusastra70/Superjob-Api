import asyncio
import websockets
import json
import uuid

async def test_chat_flow():
    # 1. Connect WebSocket
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlbXBsb3llckBzdXBlcmpvYi5jb20iLCJ1c2VyX2lkIjo4LCJleHAiOjE3NjU3MjQ1MzB9.67n7BfVsCfhE99-dV7nZzKK1bp8XmLs9ixSBVRxrsuo"
    async with websockets.connect(f"ws://localhost:8000/api/v1/ws/chat?token={token}") as websocket:
        print("✅ Connected to WebSocket")
        
        # 2. Subscribe to thread
        thread_id = "abe51f39-7c7d-448f-ab01-29aa057a0174"
        await websocket.send(json.dumps({
            "type": "subscribe",
            "thread_id": thread_id
        }))
        print(f"✅ Subscribed to thread: {thread_id}")
        
        # 3. Listen for messages
        async def listener():
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    print(f"📨 Received: {data}")
                    
                    if data.get("type") == "message:new":
                        print(f"💬 New message: {data.get('message_text')}")
                    
                except Exception as e:
                    print(f"❌ Error: {e}")
                    break
        
        # Start listener in background
        listener_task = asyncio.create_task(listener())
        
        # 4. Send typing indicator
        await websocket.send(json.dumps({
            "type": "typing",
            "thread_id": thread_id,
            "is_typing": True
        }))
        print("✍️  Sent typing indicator")
        
        await asyncio.sleep(1)
        
        # 5. Stop typing
        await websocket.send(json.dumps({
            "type": "typing",
            "thread_id": thread_id,
            "is_typing": False
        }))
        
        # Wait for messages
        await asyncio.sleep(10)
        
        # 6. Unsubscribe
        await websocket.send(json.dumps({
            "type": "unsubscribe",
            "thread_id": thread_id
        }))
        
        listener_task.cancel()

if __name__ == "__main__":
    asyncio.run(test_chat_flow())