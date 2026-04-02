import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

PORT = int(os.getenv("PORT", "9400"))
SSL_CERT_PATH = os.getenv("SSL_CERT_PATH", str(Path(__file__).parent / "certs" / "server.pem"))
SSL_KEY_PATH = os.getenv("SSL_KEY_PATH", str(Path(__file__).parent / "certs" / "server-key.pem"))
DB_PATH = os.getenv("DB_PATH", str(Path(__file__).parent / "research.db"))
