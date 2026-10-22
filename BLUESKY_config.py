# config.py

from datetime import datetime
import os  # Import os here

# --- Asset Search Terms ---
# Each inner list contains search terms for one asset.
# The *first* term is used as the primary identifier for filenames and logs.
# Include variations like "$TICKER", "#TICKER", "Company Name", etc.
STOCKS = [
    ["AAPL", "$AAPL", "#AAPL", "AAPL.MX", "#AAPL.MX", "$AAPL.MX", "AAPL.US", "#AAPL.US", "$AAPL.US", "NASDAQ:AAPL", "NASDAQGS:AAPL", "Apple Inc", "Apple", 
     "iPhone", "iPad", "AirPods", "Mac", "Apple stocks","iOS", "AAPL stocks", "Tim Cook", "Katherine Adams", "Eddy Cue", "Craig Federighi", "John Giannandrea", "Greg “Joz” Joswiak", "Sabih Khan",
     "Deirdre OBrien", "Kevan Parekh", "Johny Srouji", "John Ternus", "Jeff Williams", "Mike Fenger", "Lisa Jackson", "Luca Maestri", "Isabel Ge Mahe", "Tor Myhren", "Adrian Perica", "Kristin Huguet Quayle", "Phil Schiller"],
    
    ["MSFT", "$MSFT", "#MSFT", "MSFT.US", "#MSFT.US","$MSFT.US", "Microsoft Corporation", "Microsoft", "NASDAQ:MSFT", "NASDAQGS:MSFT", 
     "MS Windows", "MS Office", "Outlook", "Onedrive","Excel","Powerpoint","Word","Power BI","OneNote", "Teams", "Edge","Exchange", "Viva", "Copilot", "Defender","Power Apps", "Forms", "Azure Cloud", 
     "Microsoft stocks", "MSFT stocks", "Satya Nadella", "Hugh F. Johnston", "Teri L. List", "Carlos A. Rodriguez", "John W. Stanton", "Sandra E. Peterson", "Reid G. Hoffman", "Penny S. Pritzker", "Catherine MacGregor", "Mark A. L. Mason", "Charles W. Scharf", "Emma N. Walmsley"],
    
    ["AMZN", "$AMZN", "#AMZN", "AMZN.US", "#AMZN.US", "$AMZN.US", "AMZN.NE", "#AMZN.NE", "$AMZN.NE", "NASDAQ.AMZN", "NASDAQGS.AMZN","Amazon.com, Inc", "Amazon", "Amazon.com",
     "AWS", "Amazon Prime Video", "Amazon Prime", "Prime","Amazon Kindle", "Kindle", "Amazon Fire", "Amazon Studios", "Amazon Games Studios", "Amazon Luna", "Luna", "Amazon Web Services", "Amazon Basics", "AWS Identity and Access Management", "AWS IAM",
     "Amazon stocks", "AMZN stocks","Bezos", "Jeff Bezos","Jeffrey P. Bezos", "Andy Jassy", "Brian T. Olsavsky", "Matt Garman",
     "Douglas J. Herrington", "Shelley L. Reynolds", "David A. Zapolsky", "Keith B. Alexander", "Edith W. Cooper", "Jamie S. Gorelick", "Daniel P. Huttenlocher", "Andrew Y. Ng", "Indra K. Nooyi", "Jonathan J. Rubinstein", "Brad D. Smith", "Patricia Q. Stonesifer", "Wendell P. Weeks"],
    
    ["GOOG", "$GOOG", "#GOOG", "GOOGL","#GOOGL","$GOOGL", "Alphabet Inc", "Google", "NASDAQ:GOOG", "NASDAQGS:GOOG","NASDAQ:GOOGL","NASDAQGS:GOOGL",
     "Alphabet","Alphabet stocks","Google stocks","GOOG stocks","GOOGL stocks","Chrome","Android","Gemini", "Gmail","Google Calendar","Google Docs","Google Maps","Google Photos","Google Play","Pixel","Google search","Youtube","Google Cloud","Google Drive",
     "Sundar Pichai", "Sergey Brin", "Larry Page", "John Doerr", "John Hennessy", "Roger Ferguson", "Ram Shriram", "Ruth Porat", "Ann Mather", "R. Martin Chavez", "Robin Washington", "Anat Ashkenazi", "Eric Schmidt", "Kent Walker", "Philipp Schindler", "Amie OToole"],
    
    ["NVDA", "$NVDA", "#NVDA", "NVIDIA Corporation", "Nvidia", "NASDAQ:NVDA", "NASDAQGS:NVDA", 
     "Graphics", "GPU", "AI chip", "Geforce", "CUDA", "RTX", "NVS","DGX","GRID", "Rob Burgess", "Tench Coxe","John Dabiri","Persis Drell","Jensen Huang", "Dawn Hudson", "Harvey C. Jones", "Melissa B. Lora","Stephen Neal","Ellen Ochoa","Brooke Seawell",
     "Aarti Shah","Mark Stevens"]
]

CRYPTO = [
    ["BTC", "$BTC", "#BTC", "Bitcoin", "₿", "XBT", "bitcoin-core", "bitcoin network", 
     "digital gold", "store of value", "crypto’s first", "BTC/USD", "Satoshi’s coin"],
    
    ["ETH", "$ETH", "#ETH", "Ethereum", "Ξ", "ether", "ethereum network", 
     "smart-contract platform", "DeFi backbone", "gas token", "ETH/USD", 
     "Vitalik’s chain", "ERC-20 native"],
    
    ["BNB", "$BNB", "#BNB", "Binance Coin", "Binance token", "Binance Chain", 
     "BNB Chain", "exchange token", "trading fee discount", "BNB/USD", 
     "CZ’s currency", "Smart Chain gas"],
    
    ["SOL", "$SOL", "#SOL", "Solana", "SOLANA", "Solana network", 
     "high-throughput chain", "proof-of-history token", "DeFi altcoin", 
     "SOL/USD", "Ultrafast blockchain"],
    
    ["XRP", "$XRP", "#XRP", "Ripple", "Ripple token", "ripple-net asset", 
     "cross-border coin", "bank rails token", "XRP/USD", "Ripple Labs coin"]
]

# Combine the lists of lists
ASSETS = STOCKS + CRYPTO

# Total per‐asset goal over the entire period
PER_ASSET_TARGET_TOTAL = 50000  # Example: aiming for 50k total eventually
# Months in window: Jan 2023–Dec 2024 = 24
MONTHS = 24
# Calculate realistic monthly target (use ceiling or add buffer)
# Set low (e.g., 200) for testing rejection reasons, increase later for actual collection
MONTHLY_TARGET = 200  # Target for testing fetch/rejection logic

# --- Credentials ---
# Load from environment variables is strongly recommended
HANDLE = os.environ.get("BSKY_HANDLE", "tomasbakalarka826.bsky.social")
APP_PWD = os.environ.get("BSKY_APP_PWD", "V7Po4;vvEN(1")
# --- End Credentials ---

OUTPUT_DIR = "data"
LOG_FILE = "fetch_script.log"  # Define log file name
RATE_SLEEP = 0.2     # base sleep between calls
BACKOFF     = 5      # multiplier on 429 errors
FETCH_LIMIT_PER_PAGE = 50  # Max allowed by API is 100, 50 is safer
