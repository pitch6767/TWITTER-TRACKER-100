import requests
import asyncio
import websockets
import json
import sys
import time
from datetime import datetime

class MonitoringIntegrationTester:
    def __init__(self, base_url="https://crypto-spotter-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.ws_url = f"{base_url}/api/ws".replace('https://', 'wss://').replace('http://', 'ws://')
        self.test_accounts = []
        
    def api_request(self, method, endpoint, data=None):
        """Make API request"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
                
            return response.status_code == 200, response.json() if response.status_code == 200 else {}
        except Exception as e:
            print(f"API request failed: {e}")
            return False, {}
    
    def test_monitoring_system_status(self):
        """Test the current monitoring system status"""
        print("🔍 Testing Monitoring System Status")
        
        success, status = self.api_request('GET', 'monitoring/status')
        if success:
            print(f"✅ Monitoring Status Retrieved:")
            print(f"   Is Monitoring: {status.get('is_monitoring', False)}")
            print(f"   Monitored Accounts: {status.get('monitored_accounts_count', 0)}")
            print(f"   Alert Threshold: {status.get('alert_threshold', 'Unknown')}")
            print(f"   Monitoring Type: {status.get('monitoring_type', 'Unknown')}")
            print(f"   Last Check: {status.get('last_check', 'Never')}")
            print(f"   Known Tokens Filtered: {status.get('known_tokens_filtered', 0)}")
            
            accounts = status.get('accounts', [])
            if accounts:
                print(f"   Accounts being monitored: {', '.join(accounts)}")
            
            return status.get('is_monitoring', False), status
        else:
            print("❌ Failed to get monitoring status")
            return False, {}
    
    def test_add_test_accounts(self):
        """Add test accounts for monitoring"""
        print("\n👥 Adding Test Accounts for Monitoring")
        
        test_accounts_data = [
            {"username": "crypto_whale_1", "display_name": "Crypto Whale 1"},
            {"username": "meme_detector", "display_name": "Meme Detector"},
            {"username": "token_hunter_pro", "display_name": "Token Hunter Pro"}
        ]
        
        for account_data in test_accounts_data:
            success, response = self.api_request('POST', 'accounts', account_data)
            if success:
                self.test_accounts.append(response)
                print(f"✅ Added account: @{account_data['username']}")
            else:
                print(f"❌ Failed to add account: @{account_data['username']}")
        
        return len(self.test_accounts) > 0
    
    def test_start_monitoring(self):
        """Test starting the monitoring system"""
        print("\n🚀 Testing Start Monitoring")
        
        success, response = self.api_request('POST', 'monitoring/start')
        if success:
            print(f"✅ Monitoring Started:")
            print(f"   Message: {response.get('message', 'Unknown')}")
            print(f"   Accounts Count: {response.get('accounts_count', 0)}")
            print(f"   Monitoring Type: {response.get('monitoring_type', 'Unknown')}")
            print(f"   Alert Threshold: {response.get('alert_threshold', 'Unknown')}")
            return True
        else:
            print("❌ Failed to start monitoring")
            return False
    
    def test_alert_system_with_mentions(self):
        """Test the alert system by adding multiple mentions"""
        print("\n🚨 Testing Alert System with Token Mentions")
        
        # Add mentions for the same token from different accounts
        test_token = "NEWTESTCOIN"
        mentions = [
            {"token_name": test_token, "account_username": "crypto_whale_1", "tweet_url": "https://x.com/crypto_whale_1/status/1"},
            {"token_name": test_token, "account_username": "meme_detector", "tweet_url": "https://x.com/meme_detector/status/2"},
            {"token_name": test_token, "account_username": "token_hunter_pro", "tweet_url": "https://x.com/token_hunter_pro/status/3"}
        ]
        
        for mention in mentions:
            success, response = self.api_request('POST', 'mentions', mention)
            if success:
                print(f"✅ Added mention: {test_token} by @{mention['account_username']}")
            else:
                print(f"❌ Failed to add mention: {test_token} by @{mention['account_username']}")
        
        # Wait for processing
        time.sleep(3)
        
        # Check for name alerts
        success, alerts_response = self.api_request('GET', 'alerts/names')
        if success:
            alerts = alerts_response.get('alerts', [])
            new_alerts = [alert for alert in alerts if alert.get('token_name', '').upper() == test_token.upper()]
            
            if new_alerts:
                alert = new_alerts[0]
                print(f"✅ Name Alert Generated:")
                print(f"   Token: {alert.get('token_name')}")
                print(f"   Quorum Count: {alert.get('quorum_count')}")
                print(f"   Accounts: {', '.join(alert.get('accounts_mentioned', []))}")
                return True
            else:
                print(f"⚠️  No name alert found for {test_token}")
                return False
        else:
            print("❌ Failed to get name alerts")
            return False
    
    async def test_realtime_websocket_integration(self):
        """Test real-time WebSocket integration"""
        print("\n🔌 Testing Real-time WebSocket Integration")
        
        try:
            async with websockets.connect(self.ws_url) as websocket:
                print("✅ WebSocket connected")
                
                # Listen for initial state
                message = await websocket.recv()
                data = json.loads(message)
                
                if data.get('type') == 'initial_state':
                    print("✅ Received initial state via WebSocket")
                    initial_data = data.get('data', {})
                    print(f"   Name alerts in state: {len(initial_data.get('name_alerts', []))}")
                    print(f"   CA alerts in state: {len(initial_data.get('ca_alerts', []))}")
                    return True
                else:
                    print(f"⚠️  Unexpected message type: {data.get('type')}")
                    return False
                    
        except Exception as e:
            print(f"❌ WebSocket integration test failed: {e}")
            return False
    
    def test_advanced_filtering(self):
        """Test advanced filtering capabilities"""
        print("\n🛡️  Testing Advanced Filtering System")
        
        # Try to add mentions for established tokens (should be filtered)
        established_tokens = ["BTC", "ETH", "USDT", "BNB"]
        
        for token in established_tokens:
            success, response = self.api_request('POST', 'mentions', {
                "token_name": token,
                "account_username": "crypto_whale_1",
                "tweet_url": f"https://x.com/crypto_whale_1/status/{token.lower()}"
            })
            
            if success:
                print(f"✅ Added mention for established token: {token}")
            else:
                print(f"❌ Failed to add mention for: {token}")
        
        # Check monitoring status for filtering info
        success, status = self.api_request('GET', 'monitoring/status')
        if success:
            filtered_count = status.get('known_tokens_filtered', 0)
            print(f"✅ Filtering system active - {filtered_count} known tokens filtered")
            return filtered_count > 0
        
        return False
    
    def cleanup_test_data(self):
        """Clean up test accounts"""
        print("\n🧹 Cleaning up test data")
        
        for account in self.test_accounts:
            account_id = account.get('id')
            if account_id:
                success, _ = self.api_request('DELETE', f'accounts/{account_id}')
                if success:
                    print(f"✅ Deleted account: {account.get('username')}")
                else:
                    print(f"❌ Failed to delete account: {account.get('username')}")

async def main():
    print("🚀 Starting Comprehensive Monitoring Integration Test")
    print("Testing Real-time Monitoring, Alerts, WebSocket, and Filtering")
    print("=" * 70)
    
    tester = MonitoringIntegrationTester()
    
    # Test 1: Check monitoring system status
    is_monitoring, status = tester.test_monitoring_system_status()
    
    # Test 2: Add test accounts
    accounts_added = tester.test_add_test_accounts()
    
    # Test 3: Start monitoring (if not already running)
    if not is_monitoring:
        monitoring_started = tester.test_start_monitoring()
    else:
        monitoring_started = True
        print("\n✅ Monitoring already active")
    
    # Test 4: Test alert system
    alert_system_working = tester.test_alert_system_with_mentions()
    
    # Test 5: Test WebSocket integration
    websocket_working = await tester.test_realtime_websocket_integration()
    
    # Test 6: Test advanced filtering
    filtering_working = tester.test_advanced_filtering()
    
    # Cleanup
    tester.cleanup_test_data()
    
    # Results
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print(f"Monitoring System Status: {'✅ ACTIVE' if is_monitoring else '❌ INACTIVE'}")
    print(f"Test Accounts Added: {'✅ SUCCESS' if accounts_added else '❌ FAILED'}")
    print(f"Monitoring Start/Active: {'✅ SUCCESS' if monitoring_started else '❌ FAILED'}")
    print(f"Alert System: {'✅ WORKING' if alert_system_working else '❌ FAILED'}")
    print(f"WebSocket Integration: {'✅ WORKING' if websocket_working else '❌ FAILED'}")
    print(f"Advanced Filtering: {'✅ ACTIVE' if filtering_working else '❌ INACTIVE'}")
    
    # Overall assessment
    total_tests = 6
    passed_tests = sum([
        is_monitoring, accounts_added, monitoring_started, 
        alert_system_working, websocket_working, filtering_working
    ])
    
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"\nOverall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
    
    if success_rate >= 80:
        print("🎉 MONITORING SYSTEM IS WORKING EXCELLENTLY!")
        return 0
    elif success_rate >= 60:
        print("⚠️  MONITORING SYSTEM IS MOSTLY WORKING")
        return 0
    else:
        print("❌ MONITORING SYSTEM NEEDS ATTENTION")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))