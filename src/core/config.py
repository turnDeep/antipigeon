import os
import sys
import logging
import keyring
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load .env file
load_dotenv()

SERVICE_NAME = "Antipigeon"
TOKEN_KEY = "discord_bot_token"

class Config:
    def __init__(self):
        self._allowed_user_ids = self._load_allowed_user_ids()
        self._token = self._load_token()
        self.antigravity_path = os.getenv("ANTIGRAVITY_PATH", "antigravity")

    def _load_allowed_user_ids(self):
        ids_str = os.getenv("ALLOWED_USER_IDS", "")
        if not ids_str:
            logger.warning("ALLOWED_USER_IDS is not set in .env! Anyone can use this bot.")
            return []
        try:
            return [int(uid.strip()) for uid in ids_str.split(",") if uid.strip()]
        except ValueError:
            logger.error("Invalid ALLOWED_USER_IDS format. Must be comma-separated integers.")
            return []

    def _load_token(self):
        # Try keyring first
        try:
            token = keyring.get_password(SERVICE_NAME, TOKEN_KEY)
            if token:
                logger.info("Loaded Discord token from SecretStorage/Keyring.")
                return token
        except Exception as e:
            logger.warning(f"Failed to load token from keyring: {e}")

        # Fallback to env
        token = os.getenv("DISCORD_TOKEN")
        if token:
            logger.info("Loaded Discord token from .env.")
            return token

        logger.error("Discord Token not found in Keyring or .env!")
        return None

    @property
    def token(self):
        return self._token

    @property
    def allowed_user_ids(self):
        return self._allowed_user_ids

    def save_token_to_keyring(self, token: str):
        try:
            keyring.set_password(SERVICE_NAME, TOKEN_KEY, token)
            logger.info("Token saved to SecretStorage/Keyring.")
        except Exception as e:
            logger.error(f"Failed to save token to keyring: {e}")

config = Config()
