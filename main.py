import os
import json
import requests
from dotenv import load_dotenv
import webbrowser
from urllib.parse import urlencode

# Load environment variables
load_dotenv()

# ================== CONFIG ==================
CLIENT_ID = os.getenv("ETSY_CLIENT_ID")          # Your API Key (keystring)
REDIRECT_URI = os.getenv("ETSY_REDIRECT_URI")    # e.g. http://localhost:3000/oauth/redirect
SCOPES = [
    "listings_r", "listings_w",     # Read + write listings
    "transactions_r",               # Read orders/sales
    "shops_r"                       # Shop info
]

# ===========================================

def get_authorization_url():
    """Step 1: Generate OAuth authorization URL (PKCE flow)"""
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
        "state": "random_state_string_12345",   # Change this to something random
        "code_challenge": "your_code_challenge_here",  # You need to generate this properly
        "code_challenge_method": "S256"
    }
    url = f"https://www.etsy.com/oauth/connect?{urlencode(params)}"
    print("🔗 Opening authorization URL...")
    webbrowser.open(url)
    return url


def exchange_code_for_token(auth_code, code_verifier):
    """Step 2: Exchange authorization code for access token"""
    token_url = "https://api.etsy.com/v3/public/oauth/token"
    
    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "code": auth_code,
        "code_verifier": code_verifier
    }
    
    response = requests.post(token_url, data=data)
    
    if response.status_code == 200:
        token_data = response.json()
        print("✅ Token received successfully!")
        print(json.dumps(token_data, indent=2))
        
        # Save tokens to .env or a tokens.json file
        with open("tokens.json", "w") as f:
            json.dump(token_data, f, indent=2)
        return token_data
    else:
        print("❌ Error getting token:", response.text)
        return None


def test_api_call(access_token):
    """Example: Get your shop details"""
    headers = {
        "x-api-key": CLIENT_ID,
        "Authorization": f"Bearer {access_token}"
    }
    
    # Replace with your shop ID or use /openapi/v3/application/shops/__SELF__
    response = requests.get(
        "https://api.etsy.com/v3/application/shops/__SELF__",
        headers=headers
    )
    
    if response.status_code == 200:
        print("✅ Shop data retrieved successfully!")
        print(json.dumps(response.json(), indent=2))
    else:
        print("❌ API call failed:", response.text)


if __name__ == "__main__":
    print("🚀 Etsy API Personal Tool Starting...\n")
    
    # Step 1: Get authorization
    get_authorization_url()
    
    # TODO: After you authorize in browser and get redirected,
    # copy the "code" from URL and run exchange_code_for_token()
    
    print("\nAfter authorization, copy the 'code' from redirect URL and use it above.")
