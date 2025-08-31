import asyncio
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Set
from playwright.async_api import async_playwright, Browser, Page
import aiohttp
from bs4 import BeautifulSoup
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

class TokenCA:
    """Represents a token with its contract address"""
    def __init__(self, name: str, ca: str, timestamp: datetime = None):
        self.name = name.upper()
        self.ca = ca
        self.timestamp = timestamp or datetime.now(timezone.utc)

class RealTimeXMonitor:
    def __init__(self, db: AsyncIOMotorDatabase, alert_threshold: int = 2):
        self.db = db
        self.alert_threshold = alert_threshold
        self.browser: Browser = None
        self.page: Page = None
        self.is_monitoring = False
        self.monitored_accounts = []
        self.known_tokens_with_ca: Set[str] = set()
        self.token_mentions_cache = {}
        self.last_check_time = datetime.now(timezone.utc) - timedelta(hours=1)
        self.ca_watchlist: Set[str] = set()  # Active tokens to monitor for CAs
        
        # Advanced token patterns for meme coins
        self.token_patterns = [
            r'\$([A-Z]{2,10})\b',  # $TOKEN format
            r'\b([A-Z]{2,10})(?:\s+(?:coin|token|gem|to\s+the\s+moon|moon|pump|lambo|rocket|bullish|bearish|hodl|diamond\s+hands))\b',
            r'\b(PEPE|DOGE|SHIB|BONK|WIF|FLOKI|MEME|APE|WOJAK|TURBO|BRETT|POPCAT|DEGEN|MEW|BOBO|PEPE2|LADYS|BABYDOGE|DOGELON|AKITA|KISHU|SAFEMOON|HOGE|NFD|ELON|MILADY|BEN|ANDY|BART|MATT|TOSHI|HOPPY|MUMU|BENJI|POKEMON|SPURDO|BODEN|MAGA|SLERF|BOOK|MYRO|PONKE|RETARDIO|GIGACHAD|CHAD|BASED|WOJAK|AAVE|UNI|SUSHI|CAKE|BANANA|HONEY|MILK|WATER|FIRE|EARTH|WIND|THUNDER|LIGHTNING|STORM|BLAZE|FROST|ICE|SNOW|RAIN|SUN|MOON|STAR|GALAXY|COMET|METEOR|ROCKET|SPACE|ALIEN|ROBOT|NINJA|PIRATE|VIKING|KNIGHT|WARRIOR|HERO|LEGEND|KING|QUEEN|PRINCE|PRINCESS|DUKE|LORD|MASTER|BOSS|CHIEF|CAPTAIN|COMMANDER|GENERAL|ADMIRAL|EMPEROR|GOD|ZEUS|THOR|ODIN|LOKI|FREYA|VIKING|SAMURAI|SPARTA|GLADIATOR|TITAN|GIANT|DRAGON|PHOENIX|EAGLE|HAWK|WOLF|BEAR|LION|TIGER|SHARK|WHALE|DOLPHIN|OCTOPUS|SQUID|CRAB|LOBSTER|FISH|BIRD|BAT|OWL|RAVEN|CROW|SNAKE|SPIDER|SCORPION|BEE|ANT|BUTTERFLY|MOTH|LADYBUG|BEETLE|COCKROACH|FLY|MOSQUITO|WORM|SNAIL|SLUG|TURTLE|FROG|TOAD|LIZARD|GECKO|CHAMELEON|IGUANA|ALLIGATOR|CROCODILE|HIPPO|RHINO|ELEPHANT|GIRAFFE|ZEBRA|HORSE|DONKEY|MULE|COW|BULL|OX|BUFFALO|BISON|GOAT|SHEEP|LAMB|PIG|BOAR|DEER|ELK|MOOSE|CARIBOU|REINDEER|RABBIT|HARE|SQUIRREL|CHIPMUNK|BEAVER|OTTER|SEAL|WALRUS|PENGUIN|POLAR|PANDA|KOALA|KANGAROO|PLATYPUS|ECHIDNA|SLOTH|ARMADILLO|ANTEATER|HEDGEHOG|PORCUPINE|SKUNK|RACCOON|OPOSSUM|BADGER|WEASEL|FERRET|MINK|FOX|COYOTE|JACKAL|HYENA|CHEETAH|LEOPARD|JAGUAR|PUMA|LYNX|BOBCAT|SERVAL|CARACAL|OCELOT|MARGAY|JAGUARUNDI|KODKOD|ONCILLA|GUINA|SAND|DUNE|DESERT|OASIS|MIRAGE|PYRAMID|SPHINX|PHARAOH|MUMMY|TOMB|TREASURE|GOLD|SILVER|BRONZE|COPPER|IRON|STEEL|TITANIUM|PLATINUM|DIAMOND|RUBY|EMERALD|SAPPHIRE|PEARL|CRYSTAL|GEM|JEWEL|CROWN|SCEPTER|THRONE|CASTLE|PALACE|TOWER|BRIDGE|GATE|DOOR|WINDOW|WALL|ROOF|FLOOR|CEILING|ROOM|HOUSE|HOME|FAMILY|LOVE|HEART|SOUL|SPIRIT|MIND|BRAIN|DREAM|HOPE|WISH|LUCK|FORTUNE|DESTINY|FATE|KARMA|MAGIC|SPELL|CURSE|BLESSING|MIRACLE|WONDER|MYSTERY|SECRET|KEY|LOCK|CODE|PASSWORD|ACCESS|ENTER|EXIT|OPEN|CLOSE|START|STOP|GO|COME|MOVE|STAY|RUN|WALK|JUMP|FLY|SWIM|DIVE|CLIMB|FALL|RISE|UP|DOWN|LEFT|RIGHT|NORTH|SOUTH|EAST|WEST|CENTER|MIDDLE|EDGE|CORNER|SIDE|TOP|BOTTOM|FRONT|BACK|INSIDE|OUTSIDE|ABOVE|BELOW|OVER|UNDER|THROUGH|AROUND|BETWEEN|AMONG|WITHIN|WITHOUT|BEFORE|AFTER|DURING|SINCE|UNTIL|WHILE|WHEN|WHERE|WHY|HOW|WHAT|WHO|WHICH|WHOSE|WHOM|EVERYONE|SOMEONE|ANYONE|NOBODY|EVERYBODY|SOMEBODY|ANYBODY|NOTHING|EVERYTHING|SOMETHING|ANYTHING|ALL|NONE|SOME|ANY|MANY|FEW|SEVERAL|MOST|LEAST|MORE|LESS|MUCH|LITTLE|BIG|SMALL|LARGE|HUGE|TINY|GIANT|MINI|MICRO|MACRO|MEGA|GIGA|TERA|ULTRA|SUPER|HYPER|TURBO|NITRO|BOOST|POWER|ENERGY|FORCE|STRENGTH|SPEED|FAST|SLOW|QUICK|RAPID|SWIFT|FLASH|LIGHTNING|THUNDER|STORM|HURRICANE|TORNADO|TYPHOON|CYCLONE|BLIZZARD|AVALANCHE|EARTHQUAKE|TSUNAMI|VOLCANO|ERUPTION|EXPLOSION|BLAST|BOOM|BANG|CRASH|SMASH|BREAK|SHATTER|DESTROY|DEMOLISH|ANNIHILATE|OBLITERATE|VAPORIZE|EVAPORATE|MELT|FREEZE|BURN|IGNITE|FLAME|BLAZE|INFERNO|HELL|HEAVEN|PARADISE|UTOPIA|DYSTOPIA|CHAOS|ORDER|PEACE|WAR|BATTLE|FIGHT|COMBAT|CONFLICT|VICTORY|DEFEAT|WIN|LOSE|SUCCESS|FAILURE|TRIUMPH|DISASTER|CATASTROPHE|APOCALYPSE|ARMAGEDDON|JUDGMENT|DOOMSDAY|END|BEGINNING|GENESIS|CREATION|BIRTH|DEATH|LIFE|EXISTENCE|REALITY|TRUTH|LIE|FACT|FICTION|STORY|TALE|LEGEND|MYTH|FOLKLORE|HISTORY|FUTURE|PAST|PRESENT|NOW|THEN|SOON|LATER|EARLY|LATE|ON|TIME|SCHEDULE|PLAN|STRATEGY|TACTIC|METHOD|WAY|PATH|ROAD|STREET|AVENUE|BOULEVARD|HIGHWAY|FREEWAY|EXPRESSWAY|PARKWAY|LANE|ALLEY|COURT|CIRCLE|SQUARE|PLAZA|PARK|GARDEN|FOREST|JUNGLE|DESERT|MOUNTAIN|HILL|VALLEY|CANYON|CLIFF|CAVE|TUNNEL|BRIDGE|RIVER|LAKE|OCEAN|SEA|POND|STREAM|CREEK|WATERFALL|SPRING|WELL|FOUNTAIN|POOL|BEACH|SHORE|COAST|ISLAND|CONTINENT|COUNTRY|STATE|CITY|TOWN|VILLAGE|NEIGHBORHOOD|COMMUNITY|SOCIETY|CIVILIZATION|CULTURE|TRADITION|CUSTOM|RITUAL|CEREMONY|CELEBRATION|FESTIVAL|PARTY|EVENT|OCCASION|MOMENT|INSTANT|SECOND|MINUTE|HOUR|DAY|WEEK|MONTH|YEAR|DECADE|CENTURY|MILLENNIUM|ERA|AGE|EPOCH|PERIOD|PHASE|STAGE|STEP|LEVEL|DEGREE|GRADE|RANK|CLASS|CATEGORY|TYPE|KIND|SORT|VARIETY|SPECIES|BREED|RACE|ETHNICITY|NATIONALITY|CITIZENSHIP|IDENTITY|PERSONALITY|CHARACTER|TRAIT|QUALITY|ATTRIBUTE|FEATURE|ASPECT|ELEMENT|COMPONENT|PART|PIECE|FRAGMENT|SECTION|PORTION|SEGMENT|DIVISION|UNIT|ITEM|OBJECT|THING|STUFF|MATERIAL|SUBSTANCE|MATTER|ENERGY|PARTICLE|ATOM|MOLECULE|COMPOUND|MIXTURE|SOLUTION|LIQUID|SOLID|GAS|PLASMA|VACUUM|SPACE|VOID|EMPTINESS|FULLNESS|COMPLETENESS|WHOLENESS|UNITY|HARMONY|BALANCE|EQUILIBRIUM|STABILITY|INSTABILITY|CHANGE|TRANSFORMATION|EVOLUTION|REVOLUTION|INNOVATION|INVENTION|DISCOVERY|EXPLORATION|ADVENTURE|JOURNEY|TRIP|VOYAGE|EXPEDITION|MISSION|QUEST|SEARCH|HUNT|CHASE|PURSUIT|FOLLOW|LEAD|GUIDE|DIRECT|CONTROL|COMMAND|RULE|GOVERN|MANAGE|OPERATE|FUNCTION|WORK|PERFORM|ACT|BEHAVE|CONDUCT|EXECUTE|IMPLEMENT|APPLY|USE|UTILIZE|EMPLOY|HIRE|RECRUIT|TRAIN|TEACH|LEARN|STUDY|RESEARCH|INVESTIGATE|EXAMINE|ANALYZE|EVALUATE|ASSESS|JUDGE|DECIDE|CHOOSE|SELECT|PICK|PREFER|LIKE|LOVE|ADORE|CHERISH|TREASURE|VALUE|APPRECIATE|RESPECT|ADMIRE|WORSHIP|PRAISE|HONOR|CELEBRATE|COMMEMORATE|REMEMBER|RECALL|REMIND|FORGET|IGNORE|NEGLECT|ABANDON|DESERT|LEAVE|DEPART|GO|ARRIVE|COME|RETURN|COMEBACK|REVIVAL|RESURRECTION|REBIRTH|REINCARNATION|RENEWAL|REFRESH|RESTORE|REPAIR|FIX|MEND|HEAL|CURE|TREAT|MEDICINE|DRUG|PILL|TABLET|CAPSULE|INJECTION|VACCINE|ANTIDOTE|REMEDY|SOLUTION|ANSWER|RESPONSE|REPLY|REACTION|EFFECT|RESULT|OUTCOME|CONSEQUENCE|IMPACT|INFLUENCE|POWER|AUTHORITY|CONTROL|DOMINANCE|SUPREMACY|SUPERIORITY|EXCELLENCE|PERFECTION|FLAWLESSNESS|BEAUTY|ELEGANCE|GRACE|CHARM|APPEAL|ATTRACTION|MAGNETISM|CHARISMA|PERSONALITY|SPIRIT|SOUL)(?:\s+(?:coin|token|crypto|currency|money|cash|dollar|euro|yen|pound|franc|mark|ruble|peso|real|rand|rupee|dinar|dirham|riyal|shekel|won|yuan|yen|baht|dong|kip|kyat|taka|afghani|manat|som|tenge|lari|dram|leu|lev|kuna|koruna|zloty|forint|krona|krone|markka|guilder|punt|escudo|peseta|lira|drachma|denar|tolar|lat|litas|kroon|cedi|naira|shilling|birr|nakfa|leone|dalasi|ouguiya|franc|dinar|pound|pula|loti|lilangeni|rand|kwacha|metical|ariary|rupee|dollar|franc|peso|colon|quetzal|lempira|cordoba|balboa|sucre|nuevo|real|guarani|peso|uruguayo|boliviano|chileno|colombiano|venezolano|guyanese|surinamese|falkland|bermudian|cayman|jamaican|barbadian|trinidad|tobago|dominican|haitian|cuban|bahamian|canadian|american|mexican|guatemalan|belizean|salvadoran|honduran|nicaraguan|costa|rican|panamanian|ecuadorian|peruvian|brazilian|argentine|paraguayan|uruguayan|bolivian|chilean|colombian|venezuelan|guyanan|surinamer|french|british|spanish|portuguese|dutch|german|italian|swiss|austrian|belgian|luxembourg|monaco|andorran|san|marino|vatican|maltese|cypriot|greek|bulgarian|romanian|moldovan|ukrainian|belarusian|russian|estonian|latvian|lithuanian|polish|czech|slovak|hungarian|slovene|croatian|bosnian|serbian|montenegrin|albanian|macedonian|turkish|georgian|armenian|azerbaijani|kazakh|kyrgyz|tajik|turkmen|uzbek|afghan|pakistani|indian|bangladeshi|sri|lankan|maldivian|nepali|bhutanese|myanmar|thai|laotian|cambodian|vietnamese|malaysian|bruneian|singaporean|indonesian|timorese|filipino|taiwanese|chinese|japanese|south|korean|north|korean|mongolian|australian|new|zealand|fijian|papua|guinean|solomon|vanuatu|samoa|tonga|tuvalu|kiribati|nauru|marshall|micronesian|palau|hawaiian|alaskan|puerto|rican|virgin|guam|samoa|northern|mariana|cook|niue|tokelau|pitcairn|norfolk|christmas|cocos|keeling|heard|mcdonald|macquarie|antarctic|falkland|south|georgia|sandwich|tristan|cunha|ascension|saint|helena|mauritius|seychelles|comoros|madagascar|reunion|mayotte|kerguelen|crozet|amsterdam|saint|paul|prince|edward|marion|bouvet|peter|macquarie|heard|mcdonald|antarctic|ross|dependency|marie|byrd|land|queen|maud|land|enderby|land|kemp|land|mac|robertson|land|princess|elizabeth|land|wilhelm|kaiser|land|queen|mary|land|wilkes|land|adelie|land|george|land|oates|land|victoria|land|south|magnetic|pole|north|magnetic|pole|geographic|south|pole|geographic|north|pole|equator|tropic|cancer|capricorn|arctic|circle|antarctic|circle|prime|meridian|international|date|line|greenwich|mean|time|coordinated|universal|time|daylight|saving|time|standard|time|time|zone|utc|gmt|est|cst|mst|pst|edt|cdt|mdt|pdt|ast|hst|akst|akdt|nst|ndt|atlantic|pacific|mountain|central|eastern|hawaii|alaska|newfoundland|yukon|british|columbia|alberta|saskatchewan|manitoba|ontario|quebec|new|brunswick|nova|scotia|prince|edward|island|northwest|territories|nunavut|washington|oregon|california|nevada|idaho|montana|wyoming|utah|colorado|arizona|new|mexico|north|dakota|south|dakota|nebraska|kansas|oklahoma|texas|minnesota|iowa|missouri|arkansas|louisiana|wisconsin|illinois|michigan|indiana|ohio|kentucky|tennessee|mississippi|alabama|west|virginia|virginia|maryland|delaware|pennsylvania|new|jersey|new|york|connecticut|rhode|island|massachusetts|vermont|new|hampshire|maine|florida|georgia|south|carolina|north|carolina|hawaii|alaska|district|columbia|puerto|rico|virgin|islands|guam|american|samoa|northern|mariana|islands))\b'
        ]
        
        # Known old/established tokens to filter out
        self.established_tokens = {
            'BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'USDT', 'USDC', 'BUSD', 'MATIC', 'AVAX', 'DOT', 'UNI', 'LINK', 'ATOM', 'ICP', 'LTC', 'BCH', 'FIL', 'ALGO', 'VET', 'ETC', 'THETA', 'AAVE', 'MKR', 'COMP', 'SUSHI', 'SNX', 'YFI', 'CRV', 'BAL', '1INCH'
        }
        
    async def initialize_browser(self):
        """Initialize Playwright browser for X monitoring"""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-features=VizDisplayCompositor',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]
            )
            self.page = await self.browser.new_page()
            await self.page.set_viewport_size({"width": 1920, "height": 1080})
            logger.info("Browser initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            return False
            
    async def close_browser(self):
        """Close browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
            
    async def load_known_tokens_with_ca(self):
        """Load tokens that already have contract addresses to filter them out"""
        try:
            # Load from CA alerts (tokens that already have CAs)
            ca_alerts = await self.db.ca_alerts.find().to_list(1000)
            for alert in ca_alerts:
                token_name = alert.get('token_name', '').upper()
                if token_name:
                    self.known_tokens_with_ca.add(token_name)
                    
            # Add established tokens
            self.known_tokens_with_ca.update(self.established_tokens)
            
            logger.info(f"Loaded {len(self.known_tokens_with_ca)} known tokens with CAs")
        except Exception as e:
            logger.error(f"Error loading known tokens: {e}")
            
    def extract_token_names(self, text: str) -> List[str]:
        """Extract potential token names from text using advanced patterns"""
        tokens = set()
        text = text.upper()
        
        for pattern in self.token_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    token = match[0] if match[0] else (match[1] if len(match) > 1 else '')
                else:
                    token = match
                    
                token = token.upper().strip()
                
                # Filter out tokens that already have CAs or are established
                if (len(token) >= 2 and token not in self.known_tokens_with_ca and 
                    not token.isdigit() and token not in ['THE', 'AND', 'FOR', 'WITH']):
                    tokens.add(token)
                    
        return list(tokens)
        
    async def check_x_timeline_with_browser(self, account_username: str) -> List[Dict]:
        """Check X timeline using browser automation"""
        mentions = []
        try:
            # Navigate to user's X profile
            url = f"https://x.com/{account_username}"
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait for tweets to load
            await self.page.wait_for_timeout(2000)
            
            # Extract tweets from the last hour
            tweets = await self.page.evaluate("""
                () => {
                    const tweets = [];
                    const tweetElements = document.querySelectorAll('[data-testid="tweet"]');
                    
                    for (let i = 0; i < Math.min(tweetElements.length, 10); i++) {
                        const tweet = tweetElements[i];
                        const textElement = tweet.querySelector('[data-testid="tweetText"]');
                        const timeElement = tweet.querySelector('time');
                        
                        if (textElement && timeElement) {
                            const text = textElement.innerText;
                            const timestamp = timeElement.getAttribute('datetime');
                            const tweetUrl = tweet.querySelector('a[href*="/status/"]')?.href || '';
                            
                            tweets.push({
                                text: text,
                                timestamp: timestamp,
                                url: tweetUrl
                            });
                        }
                    }
                    return tweets;
                }
            """)
            
            # Process tweets and extract token mentions
            for tweet in tweets:
                if tweet['timestamp']:
                    tweet_time = datetime.fromisoformat(tweet['timestamp'].replace('Z', '+00:00'))
                    
                    # Only process tweets from the last hour
                    if tweet_time > self.last_check_time:
                        tokens = self.extract_token_names(tweet['text'])
                        
                        for token in tokens:
                            mentions.append({
                                'token_name': token,
                                'account_username': account_username,
                                'tweet_url': tweet['url'],
                                'tweet_text': tweet['text'][:200],
                                'mentioned_at': tweet_time
                            })
                            
        except Exception as e:
            logger.error(f"Error checking X timeline for {account_username}: {e}")
            
        return mentions
        
    async def check_rss_feeds(self, account_username: str) -> List[Dict]:
        """Check RSS feeds for X accounts (backup method)"""
        mentions = []
        try:
            # Try multiple RSS endpoints
            rss_urls = [
                f"https://nitter.net/{account_username}/rss",
                f"https://nitter.it/{account_username}/rss",
                f"https://twitter.com/{account_username}/rss"  # May not work
            ]
            
            async with aiohttp.ClientSession() as session:
                for rss_url in rss_urls:
                    try:
                        async with session.get(rss_url, timeout=10) as response:
                            if response.status == 200:
                                content = await response.text()
                                soup = BeautifulSoup(content, 'xml')
                                
                                for item in soup.find_all('item')[:10]:
                                    title = item.find('title')
                                    pub_date = item.find('pubDate')
                                    link = item.find('link')
                                    description = item.find('description')
                                    
                                    if title and pub_date:
                                        tweet_text = title.text
                                        if description:
                                            tweet_text += " " + description.text
                                            
                                        # Parse date
                                        try:
                                            from email.utils import parsedate_to_datetime
                                            tweet_time = parsedate_to_datetime(pub_date.text)
                                            
                                            if tweet_time > self.last_check_time:
                                                tokens = self.extract_token_names(tweet_text)
                                                
                                                for token in tokens:
                                                    mentions.append({
                                                        'token_name': token,
                                                        'account_username': account_username,
                                                        'tweet_url': link.text if link else '',
                                                        'tweet_text': tweet_text[:200],
                                                        'mentioned_at': tweet_time
                                                    })
                                        except:
                                            continue
                                            
                                break  # Success, no need to try other URLs
                                
                    except:
                        continue
                        
        except Exception as e:
            logger.error(f"Error checking RSS for {account_username}: {e}")
            
        return mentions
        
    async def scrape_with_rotating_proxies(self, account_username: str) -> List[Dict]:
        """Custom scraping with rotating proxies (backup method)"""
        mentions = []
        try:
            # List of proxy servers (you would add real proxy servers here)
            proxies = [
                None,  # No proxy
                # 'http://proxy1:port',
                # 'http://proxy2:port',
            ]
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            for proxy in proxies:
                try:
                    connector = aiohttp.TCPConnector()
                    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
                        url = f"https://x.com/{account_username}"
                        
                        async with session.get(url, proxy=proxy, timeout=15) as response:
                            if response.status == 200:
                                html = await response.text()
                                
                                # Basic HTML parsing for tweet content
                                soup = BeautifulSoup(html, 'html.parser')
                                
                                # Look for potential tweet content
                                for script in soup.find_all('script'):
                                    if script.string and 'tweet' in script.string.lower():
                                        # Extract potential token mentions from script content
                                        tokens = self.extract_token_names(script.string)
                                        
                                        for token in tokens:
                                            mentions.append({
                                                'token_name': token,
                                                'account_username': account_username,
                                                'tweet_url': f"https://x.com/{account_username}",
                                                'tweet_text': f"Extracted from {account_username}",
                                                'mentioned_at': datetime.now(timezone.utc)
                                            })
                                            
                                break  # Success
                                
                except:
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping with proxies for {account_username}: {e}")
            
        return mentions
        
    async def monitor_account(self, account_username: str) -> List[Dict]:
        """Monitor a single X account using multiple methods"""
        all_mentions = []
        
        # Method 1: Browser automation (most reliable)
        try:
            browser_mentions = await self.check_x_timeline_with_browser(account_username)
            all_mentions.extend(browser_mentions)
            logger.info(f"Found {len(browser_mentions)} mentions via browser for @{account_username}")
        except Exception as e:
            logger.error(f"Browser method failed for @{account_username}: {e}")
            
        # Method 2: RSS feeds (backup)
        if not all_mentions:
            try:
                rss_mentions = await self.check_rss_feeds(account_username)
                all_mentions.extend(rss_mentions)
                logger.info(f"Found {len(rss_mentions)} mentions via RSS for @{account_username}")
            except Exception as e:
                logger.error(f"RSS method failed for @{account_username}: {e}")
                
        # Method 3: Custom scraping (fallback)
        if not all_mentions:
            try:
                scrape_mentions = await self.scrape_with_rotating_proxies(account_username)
                all_mentions.extend(scrape_mentions)
                logger.info(f"Found {len(scrape_mentions)} mentions via scraping for @{account_username}")
            except Exception as e:
                logger.error(f"Scraping method failed for @{account_username}: {e}")
                
        return all_mentions
        
    async def get_sploofmeme_following_list(self) -> List[str]:
        """Get all accounts that @Sploofmeme follows"""
        following_accounts = []
        try:
            # Navigate to Sploofmeme's following page
            url = "https://x.com/Sploofmeme/following"
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait for the page to load
            await self.page.wait_for_timeout(3000)
            
            # Scroll and collect following accounts
            for scroll_count in range(20):  # Scroll multiple times to load more accounts
                try:
                    # Extract usernames from current view
                    usernames = await self.page.evaluate("""
                        () => {
                            const usernames = [];
                            const userElements = document.querySelectorAll('[data-testid="UserCell"] [href^="/"]');
                            
                            for (let element of userElements) {
                                const href = element.getAttribute('href');
                                if (href && href.startsWith('/') && !href.includes('/status/')) {
                                    const username = href.substring(1);
                                    if (username && !usernames.includes(username)) {
                                        usernames.push(username);
                                    }
                                }
                            }
                            return usernames;
                        }
                    """)
                    
                    # Add new usernames to our list
                    for username in usernames:
                        if username not in following_accounts and username != 'Sploofmeme':
                            following_accounts.append(username)
                    
                    # Scroll down to load more
                    await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await self.page.wait_for_timeout(2000)
                    
                    # Stop if we haven't found new accounts in the last few scrolls
                    if len(following_accounts) > 50 and scroll_count > 10:
                        break
                        
                except Exception as e:
                    logger.error(f"Error during scroll {scroll_count}: {e}")
                    break
                    
            logger.info(f"Found {len(following_accounts)} accounts that @Sploofmeme follows")
            return following_accounts[:1000]  # Limit to 1000 accounts for performance
            
        except Exception as e:
            logger.error(f"Error getting Sploofmeme's following list: {e}")
            return []

    async def ultra_fast_ca_monitoring(self):
        """ULTRA-FAST CA monitoring - checks every 2 seconds"""
        while self.is_monitoring:
            try:
                await self.check_for_trending_ca_alerts()
                await asyncio.sleep(2)  # ULTRA-FAST: Check every 2 seconds for CAs
            except Exception as e:
                logger.error(f"Error in ultra-fast CA monitoring: {e}")
                await asyncio.sleep(1)

    async def start_monitoring(self, target_account: str = "Sploofmeme"):
        """Start DUAL-SPEED monitoring: Tweets(30s) + CAs(2s)"""
        try:
            self.is_monitoring = True
            
            # Initialize browser
            await self.initialize_browser()
            
            # Get all accounts that Sploofmeme follows
            logger.info(f"Getting all accounts that @{target_account} follows...")
            following_accounts = await self.get_sploofmeme_following_list()
            
            if not following_accounts:
                logger.warning("No following accounts found, using fallback accounts")
                following_accounts = ["elonmusk", "VitalikButerin", "cz_binance", "justinsuntron"]
            
            self.monitored_accounts = following_accounts
            
            # Load known tokens with CAs
            await self.load_known_tokens_with_ca()
            
            logger.info(f"Started DUAL-SPEED monitoring: Tweets({len(following_accounts)} accounts, 30s) + CAs(2s ultra-fast)")
            
            # Start ULTRA-FAST CA monitoring in parallel
            asyncio.create_task(self.ultra_fast_ca_monitoring())
            
            # Tweet monitoring loop (30-second intervals)
            while self.is_monitoring:
                try:
                    await self.monitoring_cycle()
                    await asyncio.sleep(30)  # Tweet mentions: 30 seconds
                except Exception as e:
                    logger.error(f"Error in tweet monitoring cycle: {e}")
                    await asyncio.sleep(15)
                    
        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")
        finally:
            await self.close_browser()
            
    async def monitoring_cycle(self):
        """Single monitoring cycle - check all accounts"""
        try:
            current_time = datetime.now(timezone.utc)
            all_mentions = []
            
            # Monitor each account
            for account in self.monitored_accounts:
                try:
                    mentions = await self.monitor_account(account)
                    all_mentions.extend(mentions)
                    
                    # Small delay between accounts to avoid rate limiting
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error monitoring @{account}: {e}")
                    
            # Process all mentions for name alerts
            await self.process_mentions_for_alerts(all_mentions)
            
            # Update last check time
            self.last_check_time = current_time
            
            if all_mentions:
                logger.info(f"Monitoring cycle complete: {len(all_mentions)} new mentions found")
                
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
            
    async def process_mentions_for_alerts(self, mentions: List[Dict]):
        """Process mentions for background tracking (no visual alerts)"""
        try:
            # Store all mentions in database first
            if mentions:
                await self.db.token_mentions.insert_many(mentions)
                
            # Group mentions by token name for background tracking
            token_groups = {}
            
            for mention in mentions:
                token_name = mention['token_name'].upper()
                
                if token_name not in token_groups:
                    token_groups[token_name] = []
                    
                token_groups[token_name].append(mention)
                
            # Check each token for background tracking activation
            for token_name, token_mentions in token_groups.items():
                # Use background tracking instead of alerts
                await self.check_for_background_tracking(token_name)
                
        except Exception as e:
            logger.error(f"Error processing mentions for background tracking: {e}")
            
    async def activate_ca_monitoring(self, token_name: str, mention_count: int):
        """Activate intensive CA monitoring for a trending token"""
        try:
            # Add to CA monitoring watchlist
            await self.db.ca_monitoring_queue.insert_one({
                "token_name": token_name,
                "mention_count": mention_count,
                "activated_at": datetime.now(timezone.utc),
                "status": "active"
            })
            
            logger.info(f"🎯 CA MONITORING ACTIVATED: {token_name} ({mention_count} mentions)")
            
        except Exception as e:
            logger.error(f"Error activating CA monitoring: {e}")

    async def check_for_background_tracking(self, token_name: str):
        """Background tracking - no alerts, just CA monitoring activation"""
        try:
            # Get recent mentions of this token (last hour)
            from datetime import datetime, timedelta
            one_hour_ago = datetime.now() - timedelta(hours=1)
            
            recent_mentions = await self.db.token_mentions.find({
                "token_name": {"$regex": f"^{token_name}$", "$options": "i"},
                "mentioned_at": {"$gte": one_hour_ago},
                "processed": {"$ne": True}
            }).to_list(100)
            
            # Group by unique accounts
            unique_accounts = set()
            
            for mention in recent_mentions:
                unique_accounts.add(mention['account_username'])
                
            # If threshold met, activate CA monitoring (no visual alert)
            if len(unique_accounts) >= self.alert_threshold:
                await self.activate_ca_monitoring(token_name, len(unique_accounts))
                
                # Mark mentions as processed
                await self.db.token_mentions.update_many(
                    {"token_name": {"$regex": f"^{token_name}$", "$options": "i"}},
                    {"$set": {"processed": True}}
                )
                
                logger.info(f"🔍 BACKGROUND TRACKING: {token_name} → CA monitoring activated")
                
        except Exception as e:
            logger.error(f"Error in background tracking: {e}")

    async def check_for_trending_ca_alerts(self):
        """ULTRA-FAST: Check for new CAs using multiple sources"""
        try:
            # Get tokens being monitored for CAs
            monitored_tokens = await self.db.ca_monitoring_queue.find({
                "status": "active"
            }).to_list(100)
            
            if not monitored_tokens:
                return
                
            # Create watchlist of token names for fast lookup
            watchlist = {token['token_name'].upper() for token in monitored_tokens}
            
            # SPEED METHOD 1: Direct Pump.fun API polling
            await self.poll_pumpfun_api_direct(watchlist)
            
            # SPEED METHOD 2: Multiple WebSocket connections (if needed)
            # This runs in parallel with the main WebSocket
            
        except Exception as e:
            logger.error(f"Error in ultra-fast CA monitoring: {e}")
            
    async def poll_pumpfun_api_direct(self, watchlist: set):
        """Direct API polling to Pump.fun for maximum speed"""
        try:
            # Direct API call to Pump.fun for recent tokens
            async with aiohttp.ClientSession() as session:
                # Try multiple endpoints for redundancy
                endpoints = [
                    "https://client-api-v1.pump.fun/coins?limit=50&sort=created&includeNsfw=true",
                    "https://api.pump.fun/coins/recently-created"  # Alternative endpoint
                ]
                
                for endpoint in endpoints:
                    try:
                        async with session.get(endpoint, timeout=5) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                # Process recent tokens
                                if isinstance(data, list):
                                    tokens = data
                                elif isinstance(data, dict) and 'coins' in data:
                                    tokens = data['coins']
                                else:
                                    continue
                                    
                                for token in tokens[:20]:  # Check last 20 tokens
                                    token_name = token.get('name', '').upper()
                                    mint_address = token.get('mint', '')
                                    created_timestamp = token.get('created_timestamp', 0)
                                    
                                    # Check if token is in our watchlist
                                    if token_name in watchlist and mint_address:
                                        # Check if less than 60 seconds old
                                        current_time = datetime.now(timezone.utc).timestamp()
                                        if (current_time - created_timestamp/1000) <= 60:
                                            
                                            # FOUND TRENDING TOKEN WITH NEW CA!
                                            await self.create_trending_ca_alert(
                                                token_name, 
                                                mint_address, 
                                                token.get('marketCap', 0),
                                                created_timestamp
                                            )
                                            
                                break  # Success - no need to try other endpoints
                                
                    except Exception as e:
                        logger.debug(f"API endpoint {endpoint} failed: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error in direct API polling: {e}")
            
    async def create_trending_ca_alert(self, token_name: str, ca_address: str, market_cap: float, timestamp: int):
        """Create high-priority CA alert for trending token"""
        try:
            # Get monitoring data
            monitored_token = await self.db.ca_monitoring_queue.find_one({
                "token_name": {"$regex": f"^{token_name}$", "$options": "i"},
                "status": "active"
            })
            
            if not monitored_token:
                return
                
            # Create enhanced CA alert
            ca_alert = {
                'contract_address': ca_address,
                'token_name': token_name,
                'market_cap': market_cap,
                'photon_url': f"https://photon-sol.tinyastro.io/en/lp/{ca_address}?timeframe=1s",
                'alert_time_utc': datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                'was_trending': True,
                'mention_count': monitored_token.get('mention_count', 0),
                'priority': 'ULTRA_HIGH',
                'detection_method': 'ultra_fast_api',
                'speed_seconds': 2
            }
            
            # Store in database
            await self.db.ca_alerts.insert_one(ca_alert)
            
            # Mark monitoring as completed
            await self.db.ca_monitoring_queue.update_one(
                {"_id": monitored_token["_id"]},
                {"$set": {"status": "ca_found", "ca_found_at": datetime.now(timezone.utc)}}
            )
            
            logger.info(f"🚨⚡ ULTRA-FAST TRENDING CA: {token_name} - {ca_address} ({monitored_token.get('mention_count', 0)} mentions → CA in 2s!)")
            
            # TODO: Broadcast to WebSocket clients
            # await broadcast_to_clients({"type": "ca_alert", "data": ca_alert})
            
        except Exception as e:
            logger.error(f"Error creating trending CA alert: {e}")

    async def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
        await self.close_browser()
        logger.info("Real-time monitoring stopped")
        
    def set_alert_threshold(self, threshold: int):
        """Set the number of accounts needed to trigger an alert"""
        self.alert_threshold = threshold
        logger.info(f"Alert threshold set to {threshold} accounts")