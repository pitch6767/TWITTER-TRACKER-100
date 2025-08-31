from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
import json
import websockets
import aiohttp
import re
from pathlib import Path
import random
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid
import time

# Custom JSON encoder for datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Tweet Tracker", description="Real-time meme coin tracking from X accounts", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Global state management
active_websocket_connections: List[WebSocket] = []
name_alerts: List[Dict] = []
ca_alerts: List[Dict] = []
tracked_accounts: List[Dict] = []
performance_data: List[Dict] = []
app_versions: List[Dict] = []
blacklist_words = ["scam", "referral", "spam", "bot"]
whitelist_accounts = []
blacklist_accounts = []

# Pydantic Models
class AlertType(str, Enum):
    NAME_ALERT = "name_alert"
    CA_ALERT = "ca_alert"

class XAccount(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    display_name: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    name_alerts_contributed: int = 0
    accepted_cas_posted: int = 0
    max_gain_24h: float = 0.0

class TokenMention(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    token_name: str
    account_username: str
    tweet_url: str
    mentioned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed: bool = False

class NameAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    token_name: str
    first_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    quorum_count: int = 1
    accounts_mentioned: List[str] = []
    tweet_urls: List[str] = []
    is_active: bool = True
    alert_triggered: bool = False

class CAAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    contract_address: str
    token_name: str
    market_cap: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    photon_url: str
    alert_time_utc: str

class AppVersion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    version_number: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tag_name: Optional[str] = None
    snapshot_data: Dict[str, Any]

class XAccountMonitor:
    def __init__(self):
        self.monitored_accounts = []
        self.is_monitoring = False
        self.token_patterns = [
            r'\$[A-Z]{2,10}\b',  # $TOKEN format
            r'\b[A-Z]{2,10}(?:\s+(?:coin|token|gem|moon|pump|lambo))\b',  # TOKEN coin/token
            r'\b(?:DOGE|PEPE|SHIB|BONK|WIF|FLOKI|MEME|APE|WOJAK|TURBO|BRETT|POPCAT|DEGEN|MEW|BOBO|PEPE2|LADYS|BABYDOGE|DOGELON|AKITA|KISHU|SAFEMOON|HOGE|NFD|ELON|MILADY|BEN|ANDY|BART|MATT|TOSHI|HOPPY|MUMU|BENJI|POKEMON|SPURDO|BODEN|MAGA|SLERF|BOOK|MYRO|PONKE)\b',  # Common meme coins
        ]
        
    async def start_monitoring(self):
        """Start monitoring X accounts for token mentions"""
        self.is_monitoring = True
        logger.info("Starting X account monitoring...")
        
        # Get all active tracked accounts
        accounts = await db.x_accounts.find({"is_active": True}).to_list(1000)
        self.monitored_accounts = [acc['username'] for acc in accounts]
        
        logger.info(f"Monitoring {len(self.monitored_accounts)} X accounts")
        
        # Start monitoring loop
        asyncio.create_task(self.monitoring_loop())
        
    async def monitoring_loop(self):
        """Main monitoring loop that checks accounts periodically"""
        while self.is_monitoring:
            try:
                await self.check_accounts_for_mentions()
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)
                
    async def check_accounts_for_mentions(self):
        """Check tracked accounts for new token mentions"""
        try:
            # Simulate checking X accounts (replace with actual implementation)
            for account in self.monitored_accounts:
                # For now, simulate finding token mentions
                await self.simulate_account_check(account)
                
        except Exception as e:
            logger.error(f"Error checking accounts: {e}")
            
    async def simulate_account_check(self, account_username):
        """Simulate checking an X account for token mentions"""
        # This simulates finding token mentions from the account
        # In a real implementation, this would scrape or use alternative APIs
        
        # Randomly simulate finding tokens (for demonstration)
        if random.random() < 0.1:  # 10% chance of finding a mention
            possible_tokens = ['BONK', 'PEPE', 'DOGE', 'WIF', 'BRETT', 'POPCAT', 'MEW', 'TURBO']
            token_name = random.choice(possible_tokens)
            
            # Create a simulated tweet URL
            tweet_url = f"https://x.com/{account_username}/status/{random.randint(1000000000000000000, 9999999999999999999)}"
            
            # Add the token mention
            mention = TokenMention(
                token_name=token_name,
                account_username=account_username,
                tweet_url=tweet_url
            )
            
            await self.process_token_mention(mention)
            
    async def process_token_mention(self, mention: TokenMention):
        """Process a found token mention"""
        try:
            # Store in database
            mention_dict = mention.dict()
            await db.token_mentions.insert_one(mention_dict)
            
            logger.info(f"Found token mention: {mention.token_name} by @{mention.account_username}")
            
            # Check for name alerts
            await self.check_for_name_alerts(mention.token_name)
            
        except Exception as e:
            logger.error(f"Error processing token mention: {e}")
            
    async def check_for_name_alerts(self, token_name: str):
        """Check if this token mention should trigger a name alert"""
        try:
            # Get recent mentions of this token (last hour)
            from datetime import datetime, timedelta
            one_hour_ago = datetime.now() - timedelta(hours=1)
            
            recent_mentions = await db.token_mentions.find({
                "token_name": {"$regex": f"^{token_name}$", "$options": "i"},
                "mentioned_at": {"$gte": one_hour_ago},
                "processed": {"$ne": True}
            }).to_list(100)
            
            # Group by unique accounts
            unique_accounts = set()
            tweet_urls = []
            
            for mention in recent_mentions:
                unique_accounts.add(mention['account_username'])
                tweet_urls.append(mention['tweet_url'])
                
            # If 2+ unique accounts mentioned this token, create alert
            if len(unique_accounts) >= 2:
                name_alert = NameAlert(
                    token_name=token_name,
                    first_seen=min(mention['mentioned_at'] for mention in recent_mentions),
                    quorum_count=len(unique_accounts),
                    accounts_mentioned=list(unique_accounts),
                    tweet_urls=tweet_urls,
                    alert_triggered=True
                )
                
                # Store alert
                alert_dict = name_alert.dict()
                name_alerts.append(alert_dict)
                
                logger.info(f"🚨 NAME ALERT: {token_name} mentioned by {len(unique_accounts)} accounts")
                
                # Broadcast to clients
                await broadcast_to_clients({
                    "type": "name_alert",
                    "data": alert_dict
                })
                
                # Mark mentions as processed
                await db.token_mentions.update_many(
                    {"token_name": {"$regex": f"^{token_name}$", "$options": "i"}},
                    {"$set": {"processed": True}}
                )
                
        except Exception as e:
            logger.error(f"Error checking for name alerts: {e}")

class PumpFunWebSocketClient:
    def __init__(self):
        self.websocket_url = "wss://pumpportal.fun/api/data"
        self.websocket = None
        self.is_connected = False
        self.reconnect_delay = 5
        
    async def connect(self):
        """Connect to Pump.fun WebSocket for real-time CA alerts"""
        while True:
            try:
                logger.info("Connecting to Pump.fun WebSocket...")
                self.websocket = await websockets.connect(
                    self.websocket_url,
                    ping_interval=20,
                    ping_timeout=10
                )
                self.is_connected = True
                logger.info("Connected to Pump.fun WebSocket")
                
                # Subscribe to new token launches
                await self.subscribe_to_new_tokens()
                await self.listen_for_messages()
                
            except Exception as e:
                logger.error(f"WebSocket connection failed: {e}")
                self.is_connected = False
                await asyncio.sleep(self.reconnect_delay)
                
    async def subscribe_to_new_tokens(self):
        """Subscribe to new token creation events"""
        if self.websocket and self.is_connected:
            subscription_message = {"method": "subscribeNewToken"}
            try:
                await self.websocket.send(json.dumps(subscription_message))
                logger.info("Subscribed to new token launches")
            except Exception as e:
                logger.error(f"Failed to subscribe: {e}")
                
    async def listen_for_messages(self):
        """Process incoming messages from Pump.fun"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self.process_pump_message(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse message: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.is_connected = False
        except Exception as e:
            logger.error(f"Error in message loop: {e}")
            self.is_connected = False
            
    async def process_pump_message(self, message_data: dict):
        """Process Pump.fun messages and create CA alerts"""
        try:
            if message_data.get('type') == 'tokenCreate':
                token_data = message_data.get('data', {})
                
                # Check if token is less than 1 minute old
                created_time = datetime.now(timezone.utc)
                time_diff = (datetime.now(timezone.utc) - created_time).total_seconds()
                
                if time_diff <= 60:  # Less than 1 minute old
                    ca_alert = CAAlert(
                        contract_address=token_data.get('mint', ''),
                        token_name=token_data.get('name', 'Unknown'),
                        market_cap=token_data.get('marketCap', 0),
                        photon_url=f"https://photon-sol.tinyastro.io/en/lp/{token_data.get('mint', '')}",
                        alert_time_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                    )
                    
                    ca_alerts.append(ca_alert.dict())
                    logger.info(f"New CA Alert: {ca_alert.token_name} - {ca_alert.contract_address}")
                    
                    # Broadcast to connected clients
                    await broadcast_to_clients({
                        "type": "ca_alert",
                        "data": ca_alert.dict()
                    })
                    
        except Exception as e:
            logger.error(f"Error processing Pump.fun message: {e}")

# Initialize WebSocket client and X monitor
pump_client = PumpFunWebSocketClient()
x_monitor = XAccountMonitor()

async def broadcast_to_clients(data: dict):
    """Broadcast data to all connected WebSocket clients"""
    if active_websocket_connections:
        disconnected_clients = []
        for connection in active_websocket_connections:
            try:
                await connection.send_text(json.dumps(data, cls=DateTimeEncoder))
            except Exception:
                disconnected_clients.append(connection)
                
        for connection in disconnected_clients:
            active_websocket_connections.remove(connection)

async def check_name_alerts(token_mentions: List[TokenMention], threshold: int = 2):
    """Check if token mentions meet alert threshold"""
    token_counts = {}
    
    for mention in token_mentions:
        if not mention.processed:
            token_name = mention.token_name.lower()
            if token_name not in token_counts:
                token_counts[token_name] = {
                    'count': 0,
                    'accounts': [],
                    'urls': [],
                    'first_seen': mention.mentioned_at
                }
            
            token_counts[token_name]['count'] += 1
            token_counts[token_name]['accounts'].append(mention.account_username)
            token_counts[token_name]['urls'].append(mention.tweet_url)
            
            if token_counts[token_name]['count'] >= threshold:
                # Create name alert
                name_alert = NameAlert(
                    token_name=mention.token_name,
                    first_seen=token_counts[token_name]['first_seen'],
                    quorum_count=token_counts[token_name]['count'],
                    accounts_mentioned=token_counts[token_name]['accounts'],
                    tweet_urls=token_counts[token_name]['urls'],
                    alert_triggered=True
                )
                
                name_alerts.append(name_alert.dict())
                logger.info(f"Name Alert Triggered: {name_alert.token_name} ({name_alert.quorum_count} mentions)")
                
                # Broadcast to clients
                await broadcast_to_clients({
                    "type": "name_alert",
                    "data": name_alert.dict()
                })
                
                # Mark mentions as processed
                for mention in token_mentions:
                    if mention.token_name.lower() == token_name:
                        mention.processed = True

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Tweet Tracker API", "version": "1.0.0"}

@api_router.get("/accounts", response_model=List[XAccount])
async def get_tracked_accounts():
    """Get list of tracked X accounts"""
    accounts = await db.x_accounts.find().to_list(1000)
    return [XAccount(**account) for account in accounts]

@api_router.post("/accounts", response_model=XAccount)
async def add_tracked_account(account: XAccount):
    """Add new X account to track"""
    account_dict = account.dict()
    await db.x_accounts.insert_one(account_dict)
    tracked_accounts.append(account_dict)
    return account

@api_router.delete("/accounts/{account_id}")
async def remove_tracked_account(account_id: str):
    """Remove X account from tracking"""
    await db.x_accounts.delete_one({"id": account_id})
    global tracked_accounts
    tracked_accounts = [acc for acc in tracked_accounts if acc.get('id') != account_id]
    return {"message": "Account removed successfully"}

@api_router.post("/mentions")
async def add_token_mention(mention: TokenMention):
    """Add token mention from X account (manual input for testing)"""
    mention_dict = mention.dict()
    await db.token_mentions.insert_one(mention_dict)
    
    # Use X monitor to process the mention
    await x_monitor.process_token_mention(mention)
    
    return {"message": "Token mention added successfully"}

@api_router.post("/monitoring/start")
async def start_monitoring():
    """Start automated X account monitoring"""
    await x_monitor.start_monitoring()
    return {"message": "X account monitoring started", "accounts_count": len(x_monitor.monitored_accounts)}

@api_router.post("/monitoring/stop")
async def stop_monitoring():
    """Stop automated X account monitoring"""
    x_monitor.is_monitoring = False
    return {"message": "X account monitoring stopped"}

@api_router.get("/monitoring/status")
async def get_monitoring_status():
    """Get current monitoring status"""
    return {
        "is_monitoring": x_monitor.is_monitoring,
        "monitored_accounts_count": len(x_monitor.monitored_accounts),
        "accounts": x_monitor.monitored_accounts
    }

@api_router.get("/alerts/names")
async def get_name_alerts():
    """Get all name alerts"""
    return {"alerts": name_alerts}

@api_router.get("/alerts/cas")
async def get_ca_alerts():
    """Get all CA alerts"""
    return {"alerts": ca_alerts}

@api_router.get("/performance")
async def get_performance_data():
    """Get performance metrics for tracked accounts"""
    return {"performance": performance_data}

@api_router.post("/versions/save")
async def save_version(version: AppVersion):
    """Save current app state as a version"""
    version_dict = version.dict()
    version_dict['snapshot_data'] = {
        'tracked_accounts': tracked_accounts,
        'name_alerts': name_alerts,
        'ca_alerts': ca_alerts,
        'performance_data': performance_data,
        'blacklist_words': blacklist_words,
        'whitelist_accounts': whitelist_accounts,
        'blacklist_accounts': blacklist_accounts
    }
    
    await db.app_versions.insert_one(version_dict)
    app_versions.append(version_dict)
    
    # Keep only last 10 versions
    if len(app_versions) > 10:
        app_versions.pop(0)
        
    return {"message": "Version saved successfully", "version": version_dict}

@api_router.get("/versions")
async def get_versions():
    """Get all saved versions"""
    versions = await db.app_versions.find().to_list(100)
    return {"versions": versions}

@api_router.post("/versions/{version_id}/load")
async def load_version(version_id: str):
    """Load a specific version and restore app state"""
    version = await db.app_versions.find_one({"id": version_id})
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
        
    # Restore app state
    global tracked_accounts, name_alerts, ca_alerts, performance_data
    global blacklist_words, whitelist_accounts, blacklist_accounts
    
    snapshot = version['snapshot_data']
    tracked_accounts = snapshot.get('tracked_accounts', [])
    name_alerts = snapshot.get('name_alerts', [])
    ca_alerts = snapshot.get('ca_alerts', [])
    performance_data = snapshot.get('performance_data', [])
    blacklist_words = snapshot.get('blacklist_words', [])
    whitelist_accounts = snapshot.get('whitelist_accounts', [])
    blacklist_accounts = snapshot.get('blacklist_accounts', [])
    
    return {"message": "Version loaded successfully", "version": version}

@api_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_websocket_connections.append(websocket)
    
    try:
        # Send current state to newly connected client
        await websocket.send_text(json.dumps({
            "type": "initial_state",
            "data": {
                "name_alerts": name_alerts[-10:],
                "ca_alerts": ca_alerts[-10:],
                "tracked_accounts_count": len(tracked_accounts)
            }
        }, cls=DateTimeEncoder))
        
        while True:
            try:
                data = await websocket.receive_text()
                client_message = json.loads(data)
                
                if client_message.get('type') == 'ping':
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }, cls=DateTimeEncoder))
                    
            except Exception as e:
                logger.error(f"Error processing client message: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if websocket in active_websocket_connections:
            active_websocket_connections.remove(websocket)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Tweet Tracker...")
    
    # Start Pump.fun WebSocket client in background
    asyncio.create_task(pump_client.connect())
    
    # Start X account monitoring
    await asyncio.sleep(2)  # Give time for DB to be ready
    await x_monitor.start_monitoring()
    
    logger.info("Tweet Tracker started successfully")

@app.on_event("shutdown")
async def shutdown_db_client():
    """Cleanup on shutdown"""
    logger.info("Shutting down Tweet Tracker...")
    client.close()
    
    # Close all WebSocket connections
    for connection in active_websocket_connections:
        try:
            await connection.close()
        except Exception:
            pass