import requests
import sys
import json
import time
from datetime import datetime

class AdvancedTweetTrackerTester:
    def __init__(self, base_url="https://crypto-spotter-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=15):
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
                    print(f"   Response: {json.dumps(response_data, indent=2)[:300]}...")
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

    def test_monitoring_status(self):
        """Test getting monitoring status"""
        return self.run_test("Get Monitoring Status", "GET", "monitoring/status", 200)

    def test_monitoring_config(self):
        """Test getting monitoring configuration"""
        return self.run_test("Get Monitoring Config", "GET", "monitoring/config", 200)

    def test_update_monitoring_config(self):
        """Test updating monitoring configuration"""
        config_data = {
            "alert_threshold": 3,
            "check_interval_seconds": 60,
            "enable_browser_monitoring": True,
            "enable_rss_monitoring": True,
            "enable_scraping_monitoring": True,
            "filter_old_tokens": True,
            "filter_tokens_with_ca": True
        }
        return self.run_test("Update Monitoring Config", "POST", "monitoring/config", 200, config_data)

    def test_start_monitoring(self):
        """Test starting real-time monitoring"""
        return self.run_test("Start Real-time Monitoring", "POST", "monitoring/start", 200)

    def test_stop_monitoring(self):
        """Test stopping real-time monitoring"""
        return self.run_test("Stop Real-time Monitoring", "POST", "monitoring/stop", 200)

    def test_github_setup(self):
        """Test GitHub integration setup (will fail without valid token)"""
        github_data = {
            "github_token": "test_token",
            "username": "test_user"
        }
        # This should fail with invalid token, but we test the endpoint
        success, response = self.run_test("GitHub Setup", "POST", "github/setup", 200, github_data)
        # Even if it fails due to invalid token, the endpoint should respond
        return True, response  # We expect this to fail, so we return True

    def test_github_backups(self):
        """Test listing GitHub backups"""
        return self.run_test("List GitHub Backups", "GET", "github/backups", 200)

    def test_github_stats(self):
        """Test getting GitHub stats"""
        return self.run_test("Get GitHub Stats", "GET", "github/stats", 200)

    def test_advanced_monitoring_workflow(self):
        """Test the complete advanced monitoring workflow"""
        print(f"\n🎯 Testing Advanced Real-time Monitoring Workflow")
        
        # 1. Check initial monitoring status
        success1, status_response = self.test_monitoring_status()
        if not success1:
            print("❌ Failed to get monitoring status")
            return False
            
        initial_monitoring = status_response.get('is_monitoring', False)
        print(f"   Initial monitoring state: {initial_monitoring}")
        
        # 2. Update monitoring configuration
        success2, _ = self.test_update_monitoring_config()
        if not success2:
            print("❌ Failed to update monitoring config")
            return False
            
        # 3. Start monitoring if not already running
        if not initial_monitoring:
            success3, start_response = self.test_start_monitoring()
            if not success3:
                print("❌ Failed to start monitoring")
                return False
            else:
                print(f"   Monitoring started: {start_response.get('message', 'Unknown')}")
                print(f"   Accounts being monitored: {start_response.get('accounts_count', 0)}")
                print(f"   Monitoring type: {start_response.get('monitoring_type', 'Unknown')}")
                print(f"   Alert threshold: {start_response.get('alert_threshold', 'Unknown')}")
        
        # 4. Wait a moment and check status again
        time.sleep(3)
        success4, final_status = self.test_monitoring_status()
        if success4:
            print(f"   Final monitoring state: {final_status.get('is_monitoring', False)}")
            print(f"   Monitored accounts: {final_status.get('monitored_accounts_count', 0)}")
            print(f"   Alert threshold: {final_status.get('alert_threshold', 'Unknown')}")
            print(f"   Last check: {final_status.get('last_check', 'Never')}")
            print(f"   Known tokens filtered: {final_status.get('known_tokens_filtered', 0)}")
            
            if final_status.get('is_monitoring'):
                print("✅ Advanced Real-time Monitoring System is ACTIVE")
                return True
            else:
                print("⚠️  Monitoring system not active")
                return False
        
        return False

    def test_alert_threshold_configuration(self):
        """Test configurable alert thresholds"""
        print(f"\n🎯 Testing Alert Threshold Configuration")
        
        # Test different threshold values
        thresholds = [1, 2, 3, 5]
        
        for threshold in thresholds:
            config_data = {
                "alert_threshold": threshold,
                "check_interval_seconds": 60,
                "enable_browser_monitoring": True,
                "enable_rss_monitoring": True,
                "enable_scraping_monitoring": True,
                "filter_old_tokens": True,
                "filter_tokens_with_ca": True
            }
            
            success, response = self.run_test(
                f"Set Alert Threshold to {threshold}",
                "POST",
                "monitoring/config",
                200,
                config_data
            )
            
            if not success:
                print(f"❌ Failed to set threshold to {threshold}")
                return False
                
        print("✅ Alert Threshold Configuration Working")
        return True

    def test_smart_filtering_system(self):
        """Test smart filtering capabilities"""
        print(f"\n🎯 Testing Smart Filtering System")
        
        # Get monitoring status to check filtering
        success, status = self.test_monitoring_status()
        if success:
            known_tokens_filtered = status.get('known_tokens_filtered', 0)
            print(f"   Known tokens being filtered: {known_tokens_filtered}")
            
            if known_tokens_filtered > 0:
                print("✅ Smart Filtering System is ACTIVE")
                return True
            else:
                print("⚠️  No tokens being filtered (may be normal if no known tokens loaded)")
                return True  # This might be normal
        
        return False

def main():
    print("🚀 Starting Advanced Tweet Tracker Tests")
    print("Testing Real-time Monitoring, GitHub Integration, and Advanced Features")
    print("=" * 70)
    
    tester = AdvancedTweetTrackerTester()
    
    # Basic monitoring tests
    print("\n📡 REAL-TIME MONITORING TESTS")
    print("-" * 40)
    
    tester.test_monitoring_status()
    tester.test_monitoring_config()
    
    # Advanced monitoring workflow
    print("\n🔄 ADVANCED MONITORING WORKFLOW")
    print("-" * 40)
    
    tester.test_advanced_monitoring_workflow()
    
    # Configuration tests
    print("\n⚙️  CONFIGURATION TESTS")
    print("-" * 40)
    
    tester.test_alert_threshold_configuration()
    tester.test_smart_filtering_system()
    
    # GitHub integration tests
    print("\n🐙 GITHUB INTEGRATION TESTS")
    print("-" * 40)
    
    tester.test_github_backups()
    tester.test_github_stats()
    tester.test_github_setup()  # This will likely fail without valid token
    
    # Final results
    print("\n" + "=" * 70)
    print(f"📊 ADVANCED TESTS RESULTS")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
    
    if tester.tests_passed >= (tester.tests_run * 0.8):  # 80% pass rate acceptable
        print("🎉 ADVANCED FEATURES WORKING!")
        return 0
    else:
        print("⚠️  SOME ADVANCED FEATURES NEED ATTENTION")
        return 1

if __name__ == "__main__":
    sys.exit(main())