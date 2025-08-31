import asyncio
import websockets
import json
import sys
from datetime import datetime

class WebSocketTester:
    def __init__(self, ws_url="wss://crypto-spotter-1.preview.emergentagent.com/api/ws"):
        self.ws_url = ws_url
        self.messages_received = []
        self.connection_established = False
        
    async def test_websocket_connection(self):
        """Test WebSocket connection and real-time updates"""
        try:
            print(f"🔌 Connecting to WebSocket: {self.ws_url}")
            
            async with websockets.connect(self.ws_url) as websocket:
                self.connection_established = True
                print("✅ WebSocket connection established")
                
                # Send ping message
                ping_message = {
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(ping_message))
                print("📤 Sent ping message")
                
                # Listen for messages for 10 seconds
                try:
                    async with asyncio.timeout(10):
                        while True:
                            message = await websocket.recv()
                            data = json.loads(message)
                            self.messages_received.append(data)
                            
                            print(f"📥 Received message: {data.get('type', 'unknown')}")
                            
                            if data.get('type') == 'pong':
                                print("✅ Received pong response")
                            elif data.get('type') == 'initial_state':
                                print("✅ Received initial state")
                                initial_data = data.get('data', {})
                                print(f"   Name alerts: {len(initial_data.get('name_alerts', []))}")
                                print(f"   CA alerts: {len(initial_data.get('ca_alerts', []))}")
                                print(f"   Tracked accounts: {initial_data.get('tracked_accounts_count', 0)}")
                            elif data.get('type') == 'name_alert':
                                print("🚨 Received name alert!")
                                alert_data = data.get('data', {})
                                print(f"   Token: {alert_data.get('token_name')}")
                                print(f"   Mentions: {alert_data.get('quorum_count')}")
                            elif data.get('type') == 'ca_alert':
                                print("⚡ Received CA alert!")
                                alert_data = data.get('data', {})
                                print(f"   Token: {alert_data.get('token_name')}")
                                print(f"   Contract: {alert_data.get('contract_address')}")
                                
                except asyncio.TimeoutError:
                    print("⏰ WebSocket test timeout (10 seconds)")
                    
        except websockets.exceptions.ConnectionClosed:
            print("❌ WebSocket connection closed unexpectedly")
            return False
        except Exception as e:
            print(f"❌ WebSocket connection failed: {e}")
            return False
            
        return True
        
    def print_results(self):
        """Print test results"""
        print(f"\n📊 WebSocket Test Results:")
        print(f"Connection established: {self.connection_established}")
        print(f"Messages received: {len(self.messages_received)}")
        
        if self.messages_received:
            print(f"\nMessage types received:")
            message_types = {}
            for msg in self.messages_received:
                msg_type = msg.get('type', 'unknown')
                message_types[msg_type] = message_types.get(msg_type, 0) + 1
                
            for msg_type, count in message_types.items():
                print(f"  - {msg_type}: {count}")
                
        return self.connection_established and len(self.messages_received) > 0

async def main():
    print("🚀 Starting WebSocket Real-time Updates Test")
    print("=" * 50)
    
    tester = WebSocketTester()
    
    # Test WebSocket connection
    success = await tester.test_websocket_connection()
    
    # Print results
    overall_success = tester.print_results()
    
    if overall_success:
        print("\n🎉 WebSocket real-time updates are working!")
        return 0
    else:
        print("\n⚠️  WebSocket functionality needs attention")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))