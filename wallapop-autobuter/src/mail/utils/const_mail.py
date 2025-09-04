from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "..", "..", "..", "input", "base.txt")
CONFIG_FILE = os.path.join(BASE_DIR, "..", "..", "..", "input", "config.txt")
SAMOREGI_FILE = os.path.join(BASE_DIR, "..", "..", "..", "input", "samoregi.txt")

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
RESULT_DIR = os.path.join(BASE_DIR, "..", "..", "..", "logs", "mail_logs", timestamp)
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "..", "..", "output")
COOKIE_DIR = os.path.join(OUTPUT_DIR, "cookies")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "output.txt")
OUTPUT_FILE_ERROR = os.path.join(OUTPUT_DIR, "errors.txt")
CSV_FILE_PATH = os.path.join(BASE_DIR, "..", "..", "..", "contacts.csv")