from os import getenv
from dotenv import load_dotenv

load_dotenv()

TOKEN = getenv("TOKEN")
PG_USER = getenv("PG_USER")
PG_PASS = getenv("PG_PASS")
PG_HOST = getenv("PG_HOST")
CURATOR_PASS = getenv("CURATOR_PASS")
SHEET_URL = getenv("SHEET_URL")
