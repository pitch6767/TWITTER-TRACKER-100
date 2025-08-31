import requests
import sys
import json
import time
from datetime import datetime

class TweetTrackerAPITester:
    def __init__(self, base_url="https://crypto-spotter-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_accounts = []
        self.test_mentions = []

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=10):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

            print(f"   Status Code: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - {name}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ FAILED - {name}")
                print(f"   Expected status: {expected_status}, got: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error response: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"   Error text: {response.text}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ FAILED - {name} - Request timed out after {timeout}s")
            return False, {}
        except requests.exceptions.ConnectionError:
            print(f"❌ FAILED - {name} - Connection error")
            return False, {}
        except Exception as e:
            print(f"❌ FAILED - {name} - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test("Root API Endpoint", "GET", "", 200)

    def test_get_accounts(self):
        """Test getting tracked accounts"""
        return self.run_test("Get Tracked Accounts", "GET", "accounts", 200)

    def test_add_account(self, username, display_name):
        """Test adding a new tracked account"""
        account_data = {
            "username": username,
            "display_name": display_name
        }
        success, response = self.run_test(
            f"Add Account @{username}", 
            "POST", 
            "accounts", 
            200, 
            account_data
        )
        if success and 'id' in response:
            self.test_accounts.append(response)
            return True, response
        return False, {}

    def test_add_token_mention(self, token_name, account_username, tweet_url):
        """Test adding a token mention"""
        mention_data = {
            "token_name": token_name,
            "account_username": account_username,
            "tweet_url": tweet_url
        }
        success, response = self.run_test(
            f"Add Token Mention: {token_name} by @{account_username}",
            "POST",
            "mentions",
            200,
            mention_data
        )
        if success:
            self.test_mentions.append(mention_data)
        return success, response

    def test_get_name_alerts(self):
        """Test getting name alerts"""
        return self.run_test("Get Name Alerts", "GET", "alerts/names", 200)

    def test_get_ca_alerts(self):
        """Test getting CA alerts"""
        return self.run_test("Get CA Alerts", "GET", "alerts/cas", 200)

    def test_get_performance(self):
        """Test getting performance data"""
        return self.run_test("Get Performance Data", "GET", "performance", 200)

    def test_save_version(self):
        """Test saving a version"""
        version_data = {
            "version_number": f"test_v{int(time.time())}",
            "tag_name": f"Test Version {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
        return self.run_test("Save Version", "POST", "versions/save", 200, version_data)

    def test_get_versions(self):
        """Test getting versions"""
        return self.run_test("Get Versions", "GET", "versions", 200)

    def test_name_alert_system(self):
        """Test the name alert system by adding multiple mentions of same token"""
        print(f"\n🎯 Testing Name Alert System (threshold: 2+ accounts)")
        
        # Add first account and mention
        success1, account1 = self.test_add_account("test_user_1", "Test User 1")
        if not success1:
            print("❌ Failed to add first test account")
            return False
            
        success2, _ = self.test_add_token_mention("TESTCOIN", "test_user_1", "https://x.com/test1")
        if not success2:
            print("❌ Failed to add first token mention")
            return False

        # Add second account and mention (same token)
        success3, account2 = self.test_add_account("test_user_2", "Test User 2")
        if not success3:
            print("❌ Failed to add second test account")
            return False
            
        success4, _ = self.test_add_token_mention("TESTCOIN", "test_user_2", "https://x.com/test2")
        if not success4:
            print("❌ Failed to add second token mention")
            return False

        # Wait a moment for processing
        time.sleep(2)
        
        # Check if name alert was triggered
        success5, alerts_response = self.test_get_name_alerts()
        if success5:
            alerts = alerts_response.get('alerts', [])
            testcoin_alerts = [alert for alert in alerts if alert.get('token_name', '').upper() == 'TESTCOIN']
            
            if testcoin_alerts:
                alert = testcoin_alerts[0]
                if alert.get('quorum_count', 0) >= 2:
                    print("✅ Name Alert System Working - Alert triggered with 2+ mentions")
                    return True
                else:
                    print(f"⚠️  Name Alert found but quorum_count is {alert.get('quorum_count', 0)}")
            else:
                print("⚠️  No name alert found for TESTCOIN")
        
        print("❌ Name Alert System may not be working properly")
        return False

    def cleanup_test_data(self):
        """Clean up test accounts (if delete endpoint exists)"""
        print(f"\n🧹 Cleaning up test data...")
        for account in self.test_accounts:
            account_id = account.get('id')
            if account_id:
                success, _ = self.run_test(
                    f"Delete Account {account_id}",
                    "DELETE",
                    f"accounts/{account_id}",
                    200
                )

def main():
    print("🚀 Starting Tweet Tracker API Tests")
    print("=" * 50)
    
    tester = TweetTrackerAPITester()
    
    # Basic API tests
    print("\n📋 BASIC API TESTS")
    print("-" * 30)
    
    tester.test_root_endpoint()
    tester.test_get_accounts()
    tester.test_get_name_alerts()
    tester.test_get_ca_alerts()
    tester.test_get_performance()
    tester.test_get_versions()
    
    # Account management tests
    print("\n👥 ACCOUNT MANAGEMENT TESTS")
    print("-" * 30)
    
    tester.test_add_account("crypto_trader_1", "Crypto Trader 1")
    tester.test_add_account("meme_hunter", "Meme Hunter")
    
    # Token mention tests
    print("\n💬 TOKEN MENTION TESTS")
    print("-" * 30)
    
    tester.test_add_token_mention("DOGE", "crypto_trader_1", "https://x.com/crypto_trader_1/status/123")
    tester.test_add_token_mention("PEPE", "meme_hunter", "https://x.com/meme_hunter/status/456")
    
    # Version management tests
    print("\n📦 VERSION MANAGEMENT TESTS")
    print("-" * 30)
    
    tester.test_save_version()
    tester.test_get_versions()
    
    # Name alert system test
    print("\n🚨 NAME ALERT SYSTEM TEST")
    print("-" * 30)
    
    tester.test_name_alert_system()
    
    # Cleanup
    tester.cleanup_test_data()
    
    # Final results
    print("\n" + "=" * 50)
    print(f"📊 FINAL RESULTS")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED - Check logs above")
        return 1

if __name__ == "__main__":
    sys.exit(main())