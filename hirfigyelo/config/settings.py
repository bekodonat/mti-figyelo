import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Database
DB_PATH = DATA_DIR / "news_database.db"

# Outlets config file
OUTLETS_CONFIG_PATH = CONFIG_DIR / "outlets.json"

# MTI Settings
MTI_BASE_URL = "https://mti.hu"
MTI_HOT_WINDOW_HOURS = 12
MTI_USERNAME = os.environ.get("MTI_USERNAME", "bekodonat44@gmail.com")
MTI_PASSWORD = os.environ.get("MTI_PASSWORD", "kBjngu2y2WQnv3A")

# HTTP Settings
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "hu-HU,hu;q=0.9,en-US;q=0.8,en;q=0.7",
}
REQUEST_TIMEOUT = 12.0

# Matching Engine Settings
# Ha a cikk NEM hivatkozik MTI-re, szigorúbb (0.75) hasonlóság kell a téves párosítások elkerülésére
SIMILARITY_THRESHOLD = 0.75

# Google Sheet Sync Settings
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1h1Or2v-4wayuVQDSO6DjNp90pjJZJvVb08xE9c9b_XY/edit?usp=sharing"
GOOGLE_SHEET_WEBHOOK_URL = os.environ.get(
    "GOOGLE_SHEET_WEBHOOK_URL",
    "https://script.google.com/macros/s/AKfycbyPh-puqT2HKgpGSmttleFhlLlRGVxdNQOE-FdrFJubiA-WbKJC2Vtiy2SVrw77YzeU/exec"
)
