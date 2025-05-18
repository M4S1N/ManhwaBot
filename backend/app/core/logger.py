from loguru import logger
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

LOG_DIR = os.getenv("LOG_DIR", "logs")  # Default log directory
LOG_PATH = os.path.join(LOG_DIR, "app.log")

# Create log directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

# Configure Loguru logger
logger.add(
    LOG_PATH,
    rotation="1 week",       # Create a new log file every week
    retention="1 month",     # Keep log files for 1 month
    compression="zip",       # Compress old log files
    level="INFO",            # Minimum log level
    enqueue=True,            # Recommended for async apps
    backtrace=True,          # Show full tracebacks for errors
    diagnose=True            # Provide detailed error diagnostics
)
