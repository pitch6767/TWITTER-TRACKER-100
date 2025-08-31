import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import { Bell, Activity, Users, TrendingUp, Save, RotateCcw, Settings, AlertTriangle, ExternalLink, Clock, DollarSign, Github, Zap, Filter, Shield } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { toast } from './hooks/use-toast';
import { Toaster } from './components/ui/toaster';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const WS_URL = `${BACKEND_URL}/api/ws`.replace('https://', 'wss://').replace('http://', 'ws://');

function TweetTracker() {
  const [nameAlerts, setNameAlerts] = useState([]);
  const [caAlerts, setCaAlerts] = useState([]);
  const [trackedAccounts, setTrackedAccounts] = useState([]);
  const [performanceData, setPerformanceData] = useState([]);
  const [versions, setVersions] = useState([]);
  const [alertThreshold, setAlertThreshold] = useState(2);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [monitoringStatus, setMonitoringStatus] = useState({
    is_monitoring: false,
    monitored_accounts_count: 0,
    accounts: []
  });
  const [newAccountUsername, setNewAccountUsername] = useState('');
  const [newAccountDisplayName, setNewAccountDisplayName] = useState('');
  const [tokenMention, setTokenMention] = useState({
    token_name: '',
    account_username: '',
    tweet_url: ''
  });
  const [alertThresholdConfig, setAlertThresholdConfig] = useState(2);
  const [githubToken, setGithubToken] = useState('');
  const [githubUsername, setGithubUsername] = useState('');
  const [githubBackups, setGithubBackups] = useState([]);
  const [githubStats, setGithubStats] = useState({});
  
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  useEffect(() => {
    fetchInitialData();
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  const fetchInitialData = async () => {
    try {
      const [alertsName, alertsCA, accounts, performance, versionsData, monitoringStatusData, githubBackupsData, githubStatsData] = await Promise.all([
        fetch(`${API}/alerts/names`).then(r => r.json()),
        fetch(`${API}/alerts/cas`).then(r => r.json()),
        fetch(`${API}/accounts`).then(r => r.json()),
        fetch(`${API}/performance`).then(r => r.json()),
        fetch(`${API}/versions`).then(r => r.json()),
        fetch(`${API}/monitoring/status`).then(r => r.json()),
        fetch(`${API}/github/backups`).then(r => r.json()).catch(() => ({backups: []})),
        fetch(`${API}/github/stats`).then(r => r.json()).catch(() => ({}))
      ]);
      
      setNameAlerts(alertsName.alerts || []);
      setCaAlerts(alertsCA.alerts || []);
      setTrackedAccounts(accounts || []);
      setPerformanceData(performance.performance || []);
      setVersions(versionsData.versions || []);
      setMonitoringStatus(monitoringStatusData);
      setAlertThresholdConfig(monitoringStatusData.alert_threshold || 2);
      setGithubBackups(githubBackupsData.backups || []);
      setGithubStats(githubStatsData);
    } catch (error) {
      console.error('Error fetching initial data:', error);
      toast({
        title: "Error",
        description: "Failed to load initial data",
        variant: "destructive"
      });
    }
  };

  const connectWebSocket = () => {
    try {
      wsRef.current = new WebSocket(WS_URL);
      
      wsRef.current.onopen = () => {
        setConnectionStatus('connected');
        toast({
          title: "Connected",
          description: "Real-time alerts are now active",
        });
      };
      
      wsRef.current.onmessage = (event) => {
        const message = JSON.parse(event.data);
        
        switch (message.type) {
          case 'name_alert':
            setNameAlerts(prev => [message.data, ...prev]);
            toast({
              title: "🚨 Name Alert!",
              description: `${message.data.token_name} mentioned by ${message.data.quorum_count} accounts`,
            });
            break;
            
          case 'ca_alert':
            setCaAlerts(prev => [message.data, ...prev]);
            toast({
              title: "⚡ CA Alert!",
              description: `New token: ${message.data.token_name}`,
            });
            break;
            
          case 'initial_state':
            setNameAlerts(message.data.name_alerts || []);
            setCaAlerts(message.data.ca_alerts || []);
            break;
        }
      };
      
      wsRef.current.onclose = () => {
        setConnectionStatus('disconnected');
        reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
      };
      
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setConnectionStatus('error');
    }
  };

  const addTrackedAccount = async () => {
    if (!newAccountUsername.trim()) return;
    
    try {
      const response = await fetch(`${API}/accounts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: newAccountUsername,
          display_name: newAccountDisplayName || newAccountUsername
        })
      });
      
      if (response.ok) {
        const newAccount = await response.json();
        setTrackedAccounts(prev => [...prev, newAccount]);
        setNewAccountUsername('');
        setNewAccountDisplayName('');
        toast({
          title: "Account Added",
          description: `Now tracking @${newAccount.username}`,
        });
      }
    } catch (error) {
      console.error('Error adding account:', error);
      toast({
        title: "Error",
        description: "Failed to add account",
        variant: "destructive"
      });
    }
  };

  const addTokenMention = async () => {
    if (!tokenMention.token_name.trim() || !tokenMention.account_username.trim()) return;
    
    try {
      const response = await fetch(`${API}/mentions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tokenMention)
      });
      
      if (response.ok) {
        setTokenMention({ token_name: '', account_username: '', tweet_url: '' });
        toast({
          title: "Mention Added",
          description: `Token mention tracked: ${tokenMention.token_name}`,
        });
      }
    } catch (error) {
      console.error('Error adding mention:', error);
      toast({
        title: "Error",
        description: "Failed to add token mention",
        variant: "destructive"
      });
    }
  };

  const saveVersion = async () => {
    try {
      const response = await fetch(`${API}/versions/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          version_number: `v${Date.now()}`,
          tag_name: `Snapshot ${new Date().toLocaleString()}`
        })
      });
      
      if (response.ok) {
        const savedVersion = await response.json();
        setVersions(prev => [savedVersion.version, ...prev]);
        toast({
          title: "Version Saved",
          description: "Current state has been saved",
        });
      }
    } catch (error) {
      console.error('Error saving version:', error);
      toast({
        title: "Error",
        description: "Failed to save version",
        variant: "destructive"
      });
    }
  };

  const startMonitoring = async () => {
    try {
      const response = await fetch(`${API}/monitoring/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const result = await response.json();
        setMonitoringStatus(prev => ({
          ...prev,
          is_monitoring: true,
          monitored_accounts_count: result.accounts_count
        }));
        toast({
          title: "🚀 Monitoring Started!",
          description: `Now monitoring ${result.accounts_count} X accounts automatically`,
        });
      }
    } catch (error) {
      console.error('Error starting monitoring:', error);
      toast({
        title: "Error",
        description: "Failed to start monitoring",
        variant: "destructive"
      });
    }
  };

  const stopMonitoring = async () => {
    try {
      const response = await fetch(`${API}/monitoring/stop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        setMonitoringStatus(prev => ({
          ...prev,
          is_monitoring: false
        }));
        toast({
          title: "⏹️ Monitoring Stopped",
          description: "Automatic X account monitoring has been stopped",
        });
      }
    } catch (error) {
      console.error('Error stopping monitoring:', error);
      toast({
        title: "Error",
        description: "Failed to stop monitoring",
        variant: "destructive"
      });
    }
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
      <div className="container mx-auto p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg">
              <TrendingUp className="h-8 w-8" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                Tweet Tracker
              </h1>
              <p className="text-slate-400">Real-time meme coin monitoring</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <Badge variant={connectionStatus === 'connected' ? 'default' : 'destructive'}>
              {connectionStatus === 'connected' ? '🟢 Live' : '🔴 Offline'}
            </Badge>
            <Badge variant={monitoringStatus.is_monitoring ? 'default' : 'secondary'}>
              {monitoringStatus.is_monitoring ? '👁️ Monitoring' : '⏸️ Stopped'}
            </Badge>
            <Button onClick={saveVersion} className="bg-purple-600 hover:bg-purple-700">
              <Save className="h-4 w-4 mr-2" />
              Save Version
            </Button>
          </div>
        </div>

        {/* Main Content */}
        <Tabs defaultValue="alerts" className="space-y-6">
          <TabsList className="bg-slate-800 border-slate-700">
            <TabsTrigger value="alerts" className="data-[state=active]:bg-purple-600">
              <Bell className="h-4 w-4 mr-2" />
              Alerts
            </TabsTrigger>
            <TabsTrigger value="accounts" className="data-[state=active]:bg-purple-600">
              <Users className="h-4 w-4 mr-2" />
              Accounts ({trackedAccounts.length})
            </TabsTrigger>
            <TabsTrigger value="performance" className="data-[state=active]:bg-purple-600">
              <Activity className="h-4 w-4 mr-2" />
              Performance
            </TabsTrigger>
            <TabsTrigger value="versions" className="data-[state=active]:bg-purple-600">
              <RotateCcw className="h-4 w-4 mr-2" />
              Versions
            </TabsTrigger>
          </TabsList>

          {/* Alerts Tab */}
          <TabsContent value="alerts" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Name Alerts Window */}
              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="flex items-center text-orange-400">
                    <AlertTriangle className="h-5 w-5 mr-2" />
                    Name Alerts ({nameAlerts.length})
                  </CardTitle>
                  <CardDescription>
                    Triggered when {alertThreshold}+ accounts mention same token
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4 max-h-96 overflow-y-auto">
                    {nameAlerts.length > 0 ? nameAlerts.map((alert, index) => (
                      <div key={alert.id || index} className="p-4 bg-slate-700/50 rounded-lg border-l-4 border-orange-500">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-semibold text-orange-300">{alert.token_name}</h3>
                          <Badge variant="secondary">{alert.quorum_count} mentions</Badge>
                        </div>
                        <div className="text-sm text-slate-400 space-y-1">
                          <div className="flex items-center">
                            <Clock className="h-3 w-3 mr-1" />
                            First seen: {formatTime(alert.first_seen)}
                          </div>
                          <div>Accounts: {alert.accounts_mentioned?.join(', ')}</div>
                          {alert.tweet_urls?.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {alert.tweet_urls.slice(0, 3).map((url, idx) => (
                                <a
                                  key={idx}
                                  href={url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-xs bg-purple-600 hover:bg-purple-700 px-2 py-1 rounded flex items-center"
                                >
                                  <ExternalLink className="h-3 w-3 mr-1" />
                                  Tweet {idx + 1}
                                </a>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    )) : (
                      <div className="text-center text-slate-500 py-8">
                        <AlertTriangle className="h-12 w-12 mx-auto mb-2 opacity-50" />
                        <p>No name alerts yet</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* CA Alerts Window */}
              <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="flex items-center text-green-400">
                    <TrendingUp className="h-5 w-5 mr-2" />
                    CA Alerts ({caAlerts.length})
                  </CardTitle>
                  <CardDescription>
                    New contract addresses from Pump.fun (&lt;1 min old)
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4 max-h-96 overflow-y-auto">
                    {caAlerts.length > 0 ? caAlerts.map((alert, index) => (
                      <div key={alert.id || index} className="p-4 bg-slate-700/50 rounded-lg border-l-4 border-green-500">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-semibold text-green-300">{alert.token_name}</h3>
                          <Badge variant="outline" className="text-green-400 border-green-400">
                            <DollarSign className="h-3 w-3 mr-1" />
                            {formatCurrency(alert.market_cap)}
                          </Badge>
                        </div>
                        <div className="text-sm text-slate-400 space-y-2">
                          <div className="flex items-center">
                            <Clock className="h-3 w-3 mr-1" />
                            {alert.alert_time_utc}
                          </div>
                          <div className="font-mono text-xs bg-slate-800 p-2 rounded">
                            CA: {alert.contract_address}
                          </div>
                          <a
                            href={alert.photon_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-xs"
                          >
                            <ExternalLink className="h-3 w-3 mr-1" />
                            View Chart
                          </a>
                        </div>
                      </div>
                    )) : (
                      <div className="text-center text-slate-500 py-8">
                        <TrendingUp className="h-12 w-12 mx-auto mb-2 opacity-50" />
                        <p>No CA alerts yet</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Manual Token Mention Input */}
            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-purple-400">Add Token Mention (Manual Input)</CardTitle>
                <CardDescription>
                  Manually add token mentions from X accounts for testing
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <Label htmlFor="token-name">Token Name</Label>
                    <Input
                      id="token-name"
                      placeholder="e.g., DOGE, PEPE"
                      value={tokenMention.token_name}
                      onChange={(e) => setTokenMention(prev => ({ ...prev, token_name: e.target.value }))}
                      className="bg-slate-700 border-slate-600"
                    />
                  </div>
                  <div>
                    <Label htmlFor="account-username">Account Username</Label>
                    <Input
                      id="account-username"
                      placeholder="@username"
                      value={tokenMention.account_username}
                      onChange={(e) => setTokenMention(prev => ({ ...prev, account_username: e.target.value }))}
                      className="bg-slate-700 border-slate-600"
                    />
                  </div>
                  <div>
                    <Label htmlFor="tweet-url">Tweet URL</Label>
                    <Input
                      id="tweet-url"
                      placeholder="https://x.com/..."
                      value={tokenMention.tweet_url}
                      onChange={(e) => setTokenMention(prev => ({ ...prev, tweet_url: e.target.value }))}
                      className="bg-slate-700 border-slate-600"
                    />
                  </div>
                  <div className="flex items-end">
                    <Button onClick={addTokenMention} className="w-full bg-purple-600 hover:bg-purple-700">
                      Add Mention
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Accounts Tab */}
          <TabsContent value="accounts" className="space-y-6">
            {/* Automated Monitoring Control */}
            <Card className="bg-gradient-to-r from-green-900/30 to-blue-900/30 border-green-500/30 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-green-400 flex items-center">
                  <Activity className="h-5 w-5 mr-2" />
                  Automated X Account Monitoring
                </CardTitle>
                <CardDescription>
                  Automatically monitor all accounts that @Sploofmeme follows for token mentions
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div className="space-y-2">
                    <div className="flex items-center space-x-4">
                      <Badge variant={monitoringStatus.is_monitoring ? 'default' : 'secondary'} className="text-sm">
                        {monitoringStatus.is_monitoring ? '🟢 Active Monitoring' : '⏸️ Monitoring Stopped'}
                      </Badge>
                      <span className="text-sm text-slate-400">
                        {monitoringStatus.monitored_accounts_count} accounts being monitored
                      </span>
                    </div>
                    <p className="text-xs text-slate-500">
                      The system automatically checks all followed accounts for token mentions every minute
                    </p>
                  </div>
                  <div className="flex space-x-2">
                    {!monitoringStatus.is_monitoring ? (
                      <Button onClick={startMonitoring} className="bg-green-600 hover:bg-green-700">
                        <Activity className="h-4 w-4 mr-2" />
                        Start Monitoring
                      </Button>
                    ) : (
                      <Button onClick={stopMonitoring} variant="outline" className="border-red-500 text-red-400 hover:bg-red-500/10">
                        <Activity className="h-4 w-4 mr-2" />
                        Stop Monitoring
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-blue-400">Add X Account</CardTitle>
                <CardDescription>
                  Manually add specific X accounts to track (optional - for testing)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="username">Username</Label>
                    <Input
                      id="username"
                      placeholder="@username"
                      value={newAccountUsername}
                      onChange={(e) => setNewAccountUsername(e.target.value)}
                      className="bg-slate-700 border-slate-600"
                    />
                  </div>
                  <div>
                    <Label htmlFor="display-name">Display Name</Label>
                    <Input
                      id="display-name"
                      placeholder="Display Name"
                      value={newAccountDisplayName}
                      onChange={(e) => setNewAccountDisplayName(e.target.value)}
                      className="bg-slate-700 border-slate-600"
                    />
                  </div>
                  <div className="flex items-end">
                    <Button onClick={addTrackedAccount} className="w-full bg-blue-600 hover:bg-blue-700">
                      <Users className="h-4 w-4 mr-2" />
                      Add Account
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
              <CardHeader>
                <CardTitle>Tracked Accounts ({trackedAccounts.length})</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {trackedAccounts.map((account, index) => (
                    <div key={account.id || index} className="p-4 bg-slate-700/50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-semibold">@{account.username}</h3>
                        <Badge variant={account.is_active ? 'default' : 'secondary'}>
                          {account.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>
                      <p className="text-sm text-slate-400">{account.display_name}</p>
                      <div className="text-xs text-slate-500 mt-2">
                        Added: {formatTime(account.created_at)}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Performance Tab */}
          <TabsContent value="performance">
            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-green-400">Performance Metrics</CardTitle>
                <CardDescription>
                  Track how accounts perform with alerts and gains
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center text-slate-500 py-8">
                  <Activity className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>Performance tracking coming soon</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Versions Tab */}
          <TabsContent value="versions">
            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-purple-400">Version Management</CardTitle>
                <CardDescription>
                  Save and restore app states with full rollback capability
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center text-slate-500 py-8">
                  <RotateCcw className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>Version history will appear here</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
      
      <Toaster />
    </div>
  );
}

export default TweetTracker;