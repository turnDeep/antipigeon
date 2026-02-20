import sys
import os
import logging
from getpass import getpass

# Add the project root to sys.path so we can import src.core.config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import keyring
    from src.core.config import SERVICE_NAME, TOKEN_KEY
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure you are running this script from the project root or have dependencies installed.")
    sys.exit(1)

def setup_token():
    print("=========================================")
    print("   🐦‍⬛ Antipigeon Token Setup Wizard 🐦‍⬛   ")
    print("=========================================")
    print(f"This tool will securely store your Discord Bot Token using the system keyring.")
    print(f"Service Name: {SERVICE_NAME}")
    print(f"Key: {TOKEN_KEY}")
    print("-----------------------------------------")

    try:
        # getpass might fail in some non-interactive environments, but let's try
        token = getpass("Enter your Discord Bot Token (hidden input): ").strip()
    except Exception:
        token = input("Enter your Discord Bot Token (visible input): ").strip()

    if not token:
        print("❌ Token cannot be empty. Exiting.")
        return

    try:
        keyring.set_password(SERVICE_NAME, TOKEN_KEY, token)
        print("\n✅ Token saved successfully to SecretStorage!")
        print("You can now run the bot using `python src/bot.py`.")

        # Verify
        stored_token = keyring.get_password(SERVICE_NAME, TOKEN_KEY)
        if stored_token == token:
             print("🔍 Verification successful: Token retrieves correctly.")
        else:
             print("⚠️ Verification failed: Retrieved token does not match input.")

    except Exception as e:
        print(f"\n❌ Failed to save token to keyring: {e}")
        print("As a fallback, you can set the DISCORD_TOKEN environment variable in a .env file.")

if __name__ == "__main__":
    setup_token()
