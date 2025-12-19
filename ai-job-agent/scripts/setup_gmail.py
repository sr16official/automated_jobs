import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.gmail_client import GmailClient
import logging

def setup_gmail():
    """
    Initializes Gmail authentication and creates token.json.
    """
    logging.basicConfig(level=logging.INFO)
    print("--- Gmail Auth Setup ---")
    print("This script will open a browser for you to authorize the application.")
    print("Ensure you have 'credentials.json' in the 'config/' directory.")
    
    try:
        client = GmailClient()
        if client.service:
            print("\nSUCCESS: Gmail authentication successful! 'token.json' has been created.")
        else:
            print("\nFAILED: Authentication failed. Check logs and ensure 'credentials.json' is present.")
    except Exception as e:
        print(f"\nERROR: {e}")

if __name__ == "__main__":
    setup_gmail()
